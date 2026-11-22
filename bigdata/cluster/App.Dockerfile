FROM python:3.12-slim
RUN pip install --no-cache-dir fastapi==0.115.12 uvicorn==0.34.2 "psycopg[binary]==3.2.9" confluent-kafka==2.10.0
WORKDIR /code
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"]

