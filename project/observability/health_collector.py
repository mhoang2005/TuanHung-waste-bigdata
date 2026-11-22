"""Small lab exporter based on real HTTP, TCP, Kafka metadata and PostgreSQL checks.

Never emits a successful service observation when a check raises an exception.
The optional confluent-kafka, psycopg and psutil dependencies enrich the output;
missing dependencies are explicitly exposed as unsupported components.
"""
import argparse
import concurrent.futures
import ctypes
import datetime as dt
import json
import logging
import os
from pathlib import Path
import socket
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.request import urlopen

LOG = logging.getLogger('waste-health')
UTC = dt.timezone.utc


def iso_now():
    return dt.datetime.now(UTC).isoformat()


def escape(value):
    return str(value).replace('\\', '\\\\').replace('\n', '\\n').replace('"', '\\"')


class Metrics:
    def __init__(self):
        self.lines = []

    def gauge(self, name, value, labels=None):
        if value is None:
            return
        label_text = ''
        if labels:
            label_text = '{' + ','.join(f'{k}="{escape(v)}"' for k, v in sorted(labels.items())) + '}'
        self.lines.append(f'{name}{label_text} {float(value):.12g}')

    def render(self):
        return ('\n'.join(self.lines) + '\n').encode('utf-8')


class Collector:
    def __init__(self, config):
        self.config = config
        self.started_at = time.time()
        self.lock = threading.Lock()
        self.body = b'waste_collector_initialized 0\n'
        self.states = {}
        self.timeout = config.get('request_timeout_seconds', 3)
        self.incidents = Path(config['incidents_directory'])
        self.incidents.mkdir(parents=True, exist_ok=True)
        self.stop = threading.Event()
        self.kafka = None
        try:
            from confluent_kafka.admin import AdminClient
            self.kafka = AdminClient({'bootstrap.servers': config['kafka_bootstrap'],
                                      'socket.timeout.ms': int(self.timeout * 1000),
                                      'client.id': 'waste-health-exporter'})
        except ImportError:
            LOG.warning('confluent-kafka unavailable: Kafka metadata metrics disabled')
        try:
            import psycopg
            self.psycopg = psycopg
        except ImportError:
            self.psycopg = None
            LOG.warning('psycopg unavailable: sensor silence checks disabled')
        try:
            import psutil
            self.psutil = psutil
        except ImportError:
            self.psutil = None

    def fetch_json(self, url):
        with urlopen(url, timeout=self.timeout) as response:
            return json.load(response)

    def check_service(self, service):
        started = time.monotonic()
        try:
            if service['kind'] == 'tcp':
                with socket.create_connection((service['host'], service['port']), timeout=self.timeout):
                    pass
            else:
                self.fetch_json(service['url'])
            return service['name'], True, time.monotonic() - started, ''
        except Exception as exc:
            return service['name'], False, time.monotonic() - started, f'{type(exc).__name__}: {exc}'

    def record_state(self, service, healthy, detail=''):
        old = self.states.get(service)
        self.states[service] = healthy
        # Initial failures are recorded; initial successful startup is not an incident.
        if old == healthy or old is None and healthy:
            return
        record = {'observed_at': iso_now(), 'service': service,
                  'state': 'recovered' if healthy else 'unreachable', 'detail': detail,
                  'previous_state': None if old is None else ('healthy' if old else 'unreachable')}
        with (self.incidents / 'events.jsonl').open('a', encoding='utf-8') as handle:
            handle.write(json.dumps(record, ensure_ascii=False) + '\n')
        with (self.incidents / 'events.md').open('a', encoding='utf-8') as handle:
            handle.write(f"\n## {record['observed_at']} — {service}\n\n")
            handle.write(f"Observed state: **{record['state']}**.\n\n")
            if detail:
                handle.write(f"Check result: `{detail.replace('`', '')}`\n\n")
            handle.write('This observation reports reachability; it does not prove the underlying cause.\n')
        LOG.info('%s %s %s', service, record['state'], detail)

    def host_metrics(self, metrics):
        if self.psutil:
            memory = self.psutil.virtual_memory()
            metrics.gauge('waste_host_memory_total_bytes', memory.total)
            metrics.gauge('waste_host_memory_available_bytes', memory.available)
            metrics.gauge('waste_host_cpu_utilization_percent', self.psutil.cpu_percent(interval=None))
            metrics.gauge('waste_component_supported', 1, {'component': 'host_cpu'})
        elif os.name == 'nt':
            class MemoryStatus(ctypes.Structure):
                _fields_ = [('dwLength', ctypes.c_ulong), ('dwMemoryLoad', ctypes.c_ulong),
                            ('ullTotalPhys', ctypes.c_ulonglong), ('ullAvailPhys', ctypes.c_ulonglong),
                            ('ullTotalPageFile', ctypes.c_ulonglong), ('ullAvailPageFile', ctypes.c_ulonglong),
                            ('ullTotalVirtual', ctypes.c_ulonglong), ('ullAvailVirtual', ctypes.c_ulonglong),
                            ('ullAvailExtendedVirtual', ctypes.c_ulonglong)]
            status = MemoryStatus()
            status.dwLength = ctypes.sizeof(status)
            if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(status)):
                metrics.gauge('waste_host_memory_total_bytes', status.ullTotalPhys)
                metrics.gauge('waste_host_memory_available_bytes', status.ullAvailPhys)
            metrics.gauge('waste_component_supported', 0, {'component': 'host_cpu'})

    def hdfs_metrics(self, metrics):
        try:
            payload = self.fetch_json(self.config['hdfs_jmx'])
            observed = 0
            for bean in payload.get('beans', []):
                if bean.get('name') == 'Hadoop:service=NameNode,name=FSNamesystemState':
                    for field, metric in [('NumLiveDataNodes', 'waste_hdfs_live_datanodes'),
                                          ('NumDeadDataNodes', 'waste_hdfs_dead_datanodes'),
                                          ('BlocksTotal', 'waste_hdfs_blocks_total')]:
                        if field in bean:
                            metrics.gauge(metric, bean[field]); observed += 1
                elif bean.get('name') == 'Hadoop:service=NameNode,name=FSNamesystem':
                    for field, metric in [('UnderReplicatedBlocks', 'waste_hdfs_under_replicated_blocks'),
                                          ('MissingBlocks', 'waste_hdfs_missing_blocks'),
                                          ('CapacityTotal', 'waste_hdfs_capacity_total_bytes'),
                                          ('CapacityUsed', 'waste_hdfs_capacity_used_bytes'),
                                          ('CapacityRemaining', 'waste_hdfs_capacity_available_bytes')]:
                        if field in bean:
                            metrics.gauge(metric, bean[field]); observed += 1
                elif bean.get('name') == 'Hadoop:service=NameNode,name=NameNodeInfo':
                    # Hadoop versions expose the live node map here even if FSNamesystemState
                    # field names differ. This still counts actual observed nodes.
                    if 'LiveNodes' in bean and not any('waste_hdfs_live_datanodes ' in x for x in metrics.lines):
                        live = bean['LiveNodes']
                        live = json.loads(live) if isinstance(live, str) else live
                        metrics.gauge('waste_hdfs_live_datanodes', len(live))
            metrics.gauge('waste_component_observation_success', int(observed > 0), {'component': 'hdfs'})
        except Exception as exc:
            metrics.gauge('waste_component_observation_success', 0, {'component': 'hdfs'})
            LOG.debug('HDFS metrics: %s', exc)

    def yarn_metrics(self, metrics):
        try:
            data = self.fetch_json(self.config['yarn_metrics'])['clusterMetrics']
            for field, metric in [('activeNodes', 'waste_yarn_active_nodes'),
                                  ('appsRunning', 'waste_yarn_running_applications'),
                                  ('containersAllocated', 'waste_yarn_allocated_containers'),
                                  ('allocatedMB', 'waste_yarn_allocated_memory_mb'),
                                  ('availableMB', 'waste_yarn_available_memory_mb'),
                                  ('allocatedVirtualCores', 'waste_yarn_allocated_vcores')]:
                if field in data:
                    metrics.gauge(metric, data[field])
            base = self.config['yarn_metrics'].rsplit('/', 1)[0]
            nodes = self.fetch_json(base + '/nodes').get('nodes') or {}
            for node in nodes.get('node', []):
                labels = {'node': node['nodeHostName']}
                for field, metric in [('usedMemoryMB', 'waste_yarn_node_used_memory_mb'),
                                      ('availMemoryMB', 'waste_yarn_node_available_memory_mb'),
                                      ('usedVirtualCores', 'waste_yarn_node_used_vcores'),
                                      ('availableVirtualCores', 'waste_yarn_node_available_vcores'),
                                      ('numContainers', 'waste_yarn_node_containers')]:
                    if field in node:
                        metrics.gauge(metric, node[field], labels)
                metrics.gauge('waste_yarn_node_running', int(node['state'] == 'RUNNING'), labels)
            metrics.gauge('waste_component_observation_success', 1, {'component': 'yarn'})
        except Exception as exc:
            metrics.gauge('waste_component_observation_success', 0, {'component': 'yarn'})
            LOG.debug('YARN metrics: %s', exc)

    def kafka_metrics(self, metrics):
        metrics.gauge('waste_component_supported', int(self.kafka is not None), {'component': 'kafka_metadata'})
        if not self.kafka:
            return
        try:
            metadata = self.kafka.list_topics(topic=self.config['kafka_topic'], timeout=self.timeout)
            topic = metadata.topics.get(self.config['kafka_topic'])
            if topic is None or topic.error:
                raise RuntimeError(f'Topic metadata unavailable: {topic.error if topic else "missing topic"}')
            metrics.gauge('waste_kafka_metadata_broker_count', len(metadata.brokers))
            metrics.gauge('waste_kafka_partition_count', len(topic.partitions))
            metrics.gauge('waste_kafka_under_replicated_partitions',
                          sum(len(p.isrs) < len(p.replicas) for p in topic.partitions.values()))
            for partition_id, partition in topic.partitions.items():
                labels = {'topic': self.config['kafka_topic'], 'partition': partition_id}
                metrics.gauge('waste_kafka_partition_leader_broker', partition.leader, labels)
                metrics.gauge('waste_kafka_partition_replica_count', len(partition.replicas), labels)
                metrics.gauge('waste_kafka_partition_isr_count', len(partition.isrs), labels)
            metrics.gauge('waste_component_observation_success', 1, {'component': 'kafka_metadata'})
        except Exception as exc:
            metrics.gauge('waste_component_observation_success', 0, {'component': 'kafka_metadata'})
            LOG.debug('Kafka metadata: %s', exc)

    def spark_metrics(self, metrics):
        try:
            applications = self.fetch_json(self.config['spark_api'] + '/applications')
            for application in applications:
                application_id = application['id']
                executors = self.fetch_json(self.config['spark_api'] + f'/applications/{application_id}/executors')
                workers = [x for x in executors if x['id'] != 'driver' and x.get('isActive', True)]
                metrics.gauge('waste_spark_active_executors', len(workers), {'application': application_id})
                for executor in workers:
                    labels = {'application': application_id, 'executor': executor['id'],
                              'host': executor.get('hostPort', '').split(':')[0]}
                    for field, metric in [('totalTasks', 'waste_spark_executor_total_tasks'),
                                          ('completedTasks', 'waste_spark_executor_completed_tasks'),
                                          ('failedTasks', 'waste_spark_executor_failed_tasks'),
                                          ('totalInputBytes', 'waste_spark_executor_input_bytes'),
                                          ('memoryUsed', 'waste_spark_executor_storage_memory_bytes')]:
                        if field in executor:
                            metrics.gauge(metric, executor[field], labels)
            metrics.gauge('waste_component_observation_success', 1, {'component': 'spark'})
        except Exception as exc:
            metrics.gauge('waste_component_observation_success', 0, {'component': 'spark'})
            LOG.debug('Spark metrics: %s', exc)
        progress_file = self.config.get('progress_file')
        if progress_file and Path(progress_file).exists():
            try:
                progress = json.loads(Path(progress_file).read_text(encoding='utf-8'))
                for field, metric in [('batch_id', 'waste_stream_last_batch_id'),
                                      ('num_input_rows', 'waste_stream_batch_input_rows'),
                                      ('processed_rows_per_second', 'waste_stream_processed_rows_per_second'),
                                      ('batch_duration_ms', 'waste_stream_batch_duration_ms'),
                                      ('updated_at', 'waste_stream_last_progress_timestamp_seconds')]:
                    if field in progress:
                        metrics.gauge(metric, progress[field])
            except Exception as exc:
                LOG.debug('Spark progress file: %s', exc)

    def sensor_metrics(self, metrics):
        metrics.gauge('waste_component_supported', int(self.psycopg is not None), {'component': 'postgres_sensors'})
        if not self.psycopg:
            return
        pg = dict(self.config['postgres'])
        pg['password'] = os.environ.get(pg.pop('password_env'), '')
        pg['connect_timeout'] = int(self.timeout)
        try:
            with self.psycopg.connect(**pg) as connection:
                with connection.cursor() as cursor:
                    cursor.execute('SELECT b.bin_id,s.updated_at FROM bins b LEFT JOIN bin_status s USING(bin_id) WHERE b.active')
                    now = dt.datetime.now(UTC)
                    silent = []
                    fresh = []
                    limit = self.config.get('sensor_timeout_seconds', 120)
                    for bin_id, seen_at in cursor.fetchall():
                        if seen_at:
                            age = max(0, (now - seen_at).total_seconds())
                            metrics.gauge('waste_sensor_last_arrival_age_seconds', age, {'bin_id': bin_id})
                            (silent if age > limit else fresh).append(bin_id)
                        elif time.time() - self.started_at > limit:
                            silent.append(bin_id)
                    metrics.gauge('waste_sensor_silent_bins', len(silent))
                    for bin_id in silent:
                        cursor.execute('''INSERT INTO alerts(alert_key,bin_id,alert_type,opened_at,last_seen_at,active,detail)
                            VALUES(%s,%s,'signal_lost',now(),now(),true,%s)
                            ON CONFLICT(alert_key) DO UPDATE SET
                            opened_at=CASE WHEN alerts.active THEN alerts.opened_at ELSE excluded.opened_at END,
                            last_seen_at=excluded.last_seen_at,closed_at=NULL,active=true,detail=excluded.detail''',
                            (f'{bin_id}:signal_lost', bin_id, f'No accepted latest reading for more than {limit}s of wall clock time'))
                    if fresh:
                        cursor.execute("UPDATE alerts SET active=false,closed_at=now(),last_seen_at=now() WHERE alert_type='signal_lost' AND active AND bin_id=ANY(%s)", (fresh,))
            metrics.gauge('waste_component_observation_success', 1, {'component': 'postgres_sensors'})
            self.record_state('postgres-sensor-monitor', True)
        except Exception as exc:
            metrics.gauge('waste_component_observation_success', 0, {'component': 'postgres_sensors'})
            self.record_state('postgres-sensor-monitor', False, f'{type(exc).__name__}: {exc}')

    def collect(self):
        metrics = Metrics()
        metrics.gauge('waste_collector_initialized', 1)
        metrics.gauge('waste_collector_observation_timestamp_seconds', time.time())
        self.host_metrics(metrics)
        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
            for name, healthy, elapsed, error in pool.map(self.check_service, self.config['services']):
                metrics.gauge('waste_service_up', healthy, {'service': name})
                metrics.gauge('waste_service_probe_duration_seconds', elapsed, {'service': name})
                self.record_state(name, healthy, error)
        self.hdfs_metrics(metrics)
        self.yarn_metrics(metrics)
        self.kafka_metrics(metrics)
        self.spark_metrics(metrics)
        self.sensor_metrics(metrics)
        with self.lock:
            self.body = metrics.render()

    def loop(self):
        while not self.stop.is_set():
            start = time.monotonic()
            try:
                self.collect()
            except Exception:
                LOG.exception('Collection cycle failed')
            remaining = max(0.5, self.config.get('interval_seconds', 15) - (time.monotonic() - start))
            self.stop.wait(remaining)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', required=True)
    parser.add_argument('--once', action='store_true', help='Perform one real collection and print Prometheus text')
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
    collector = Collector(json.loads(Path(args.config).read_text(encoding='utf-8')))
    if args.once:
        collector.collect()
        print(collector.body.decode(), end='')
        return

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path not in ('/metrics', '/health'):
                self.send_error(404); return
            with collector.lock:
                body = collector.body if self.path == '/metrics' else b'ok\n'
            self.send_response(200)
            self.send_header('Content-Type', 'text/plain; version=0.0.4; charset=utf-8')
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *_):
            pass

    thread = threading.Thread(target=collector.loop, daemon=True)
    thread.start()
    server = ThreadingHTTPServer((collector.config.get('listen_host', '127.0.0.1'),
                                 collector.config.get('listen_port', 9119)), Handler)
    LOG.info('Exporter listening at http://%s:%s/metrics', *server.server_address)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        collector.stop.set()
        server.server_close()


if __name__ == '__main__':
    main()
