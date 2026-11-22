"""Render host monitoring configuration; contains no service installation code."""
import argparse
import json
from pathlib import Path


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--output', default='project/observability/runtime')
    p.add_argument('--vm1', default='192.168.200.11')
    p.add_argument('--vm2', default='192.168.200.12')
    p.add_argument('--vm3', default='192.168.200.13')
    p.add_argument('--postgres-host', default='127.0.0.1')
    p.add_argument('--postgres-port', type=int, default=5432)
    p.add_argument('--database', default='waste')
    p.add_argument('--postgres-user', default='waste')
    p.add_argument('--sensor-timeout', type=int, default=120)
    p.add_argument('--progress-file', default='')
    args = p.parse_args()
    out = Path(args.output).resolve()
    out.mkdir(parents=True, exist_ok=True)
    own = Path(__file__).resolve().parent
    ips = [args.vm1, args.vm2, args.vm3]
    services = []
    for i, ip in enumerate(ips, 1):
        services += [dict(name=f'kafka-vm{i}', kind='tcp', host=ip, port=9092),
                     dict(name=f'hdfs-datanode-vm{i}', kind='json', url=f'http://{ip}:9864/jmx'),
                     dict(name=f'yarn-nodemanager-vm{i}', kind='json', url=f'http://{ip}:8042/ws/v1/node/info')]
    services += [dict(name='hdfs-namenode', kind='json', url=f'http://{args.vm1}:9870/jmx'),
                 dict(name='yarn-resourcemanager', kind='json', url=f'http://{args.vm1}:8088/ws/v1/cluster/metrics'),
                 dict(name='spark-streaming', kind='json', url=f'http://{args.vm1}:4040/api/v1/applications')]
    config = dict(listen_host='127.0.0.1', listen_port=9119, interval_seconds=15,
                  request_timeout_seconds=3, services=services,
                  kafka_bootstrap=','.join(f'{ip}:9092' for ip in ips), kafka_topic='waste-events',
                  hdfs_jmx=f'http://{args.vm1}:9870/jmx',
                  yarn_metrics=f'http://{args.vm1}:8088/ws/v1/cluster/metrics',
                  spark_api=f'http://{args.vm1}:4040/api/v1',
                  postgres=dict(host=args.postgres_host, port=args.postgres_port,
                                dbname=args.database, user=args.postgres_user,
                                password_env='WASTE_DB_PASSWORD'),
                  sensor_timeout_seconds=args.sensor_timeout,
                  progress_file=args.progress_file, incidents_directory=str(out / 'incidents'))
    (out / 'health.json').write_text(json.dumps(config, indent=2), encoding='utf-8')
    # Minimal profile deliberately uses a single actual health exporter. Linux node/JMX
    # exporters can be added later; up=1 here means exporter reached, not all services healthy.
    (out / 'prometheus.yml').write_text('''global:
  scrape_interval: 15s
  evaluation_interval: 15s
rule_files:
  - waste-alerts.yml
scrape_configs:
  - job_name: prometheus
    static_configs:
      - targets: ['127.0.0.1:9090']
  - job_name: waste-health
    static_configs:
      - targets: ['127.0.0.1:9119']
''', encoding='utf-8')
    (out / 'waste-alerts.yml').write_text((own / 'prometheus' / 'waste-alerts.yml').read_text(encoding='utf-8'), encoding='utf-8')
    prov = out / 'provisioning'
    (prov / 'datasources').mkdir(parents=True, exist_ok=True)
    (prov / 'dashboards').mkdir(parents=True, exist_ok=True)
    (prov / 'datasources' / 'waste.yml').write_text(f'''apiVersion: 1
datasources:
  - name: Waste PostgreSQL
    uid: waste-postgres
    type: postgres
    access: proxy
    url: {args.postgres_host}:{args.postgres_port}
    user: {args.postgres_user}
    jsonData:
      database: {args.database}
      sslmode: disable
      postgresVersion: 1600
      maxOpenConns: 4
      maxIdleConns: 2
      connMaxLifetime: 14400
    secureJsonData:
      password: $WASTE_DB_PASSWORD
    editable: false
  - name: Waste Prometheus
    uid: waste-prometheus
    type: prometheus
    access: proxy
    url: http://127.0.0.1:9090
    isDefault: true
    jsonData:
      httpMethod: POST
      timeInterval: 15s
    editable: false
''', encoding='utf-8')
    dashboard_path = (own / 'grafana' / 'dashboards').as_posix()
    (prov / 'dashboards' / 'waste.yml').write_text(f'''apiVersion: 1
providers:
  - name: waste-lab
    orgId: 1
    folder: Smart Waste
    type: file
    disableDeletion: false
    updateIntervalSeconds: 30
    allowUiUpdates: false
    options:
      path: '{dashboard_path}'
''', encoding='utf-8')
    (out / 'grafana.ini').write_text(f'''[server]
http_addr = 127.0.0.1
http_port = 3000
[paths]
provisioning = {prov.as_posix()}
[analytics]
reporting_enabled = false
[users]
allow_sign_up = false
''', encoding='utf-8')
    print(f'Rendered monitoring configuration: {out}')


if __name__ == '__main__':
    main()
