import os
from datetime import timedelta, timezone

import psycopg
from psycopg.rows import dict_row

VN = timezone(timedelta(hours=7))
TOPICS = ("waste-operations", "waste-payments")


def connect():
    return psycopg.connect(os.environ["DB_DSN"], row_factory=dict_row, connect_timeout=5)


def log(conn, component, level, message):
    conn.execute("INSERT INTO system_log(component,level,message) VALUES(%s,%s,%s)",
                 (component, level, message))

