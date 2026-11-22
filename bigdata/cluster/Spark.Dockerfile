FROM apache/spark:4.0.4-scala2.13-java17-python3-ubuntu
USER root
RUN pip install --no-cache-dir "psycopg[binary]==3.2.9"
RUN mkdir -p /opt/connectors && python3 -c 'import urllib.request; from concurrent.futures import ThreadPoolExecutor; repo="https://repo.maven.apache.org/maven2/"; items=["org/apache/spark/spark-sql-kafka-0-10_2.13/4.0.4","org/apache/spark/spark-token-provider-kafka-0-10_2.13/4.0.4","org/apache/kafka/kafka-clients/3.9.1","org/apache/commons/commons-pool2/2.12.0"]; download=lambda p: urllib.request.urlretrieve(repo+p+"/"+p.split("/")[-2]+"-"+p.split("/")[-1]+".jar","/opt/connectors/"+p.split("/")[-2]+".jar"); list(ThreadPoolExecutor().map(download,items))'
USER spark

