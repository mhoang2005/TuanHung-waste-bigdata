import os
from datetime import timedelta, timezone

import psycopg
from psycopg.rows import dict_row

VN = timezone(timedelta(hours=7))
TOPICS = ("waste-operations", "waste-payments")
WATCH_IOT = ("H-0001-O", "H-0061-O", "H-0181-O", "H-0241-O")
WATCH_BINS = (
    "H-0001-O", "H-0015-R", "H-0020-O", "H-0051-O",
    "H-0061-O", "H-0101-O", "H-0110-C", "H-0120-C",
    "H-0141-R", "H-0156-C", "H-0177-R",
    "H-0181-O", "H-0196-R", "H-0205-O",
    "H-0241-O", "H-0272-C", "H-0278-O",
    "H-0337-R", "H-0340-R", "H-0346-C",
    "H-0392-R", "H-0409-O", "H-0413-R",
    "H-0465-C", "H-0469-O",
    "H-0492-R", "H-0509-C", "H-0525-R",
    "H-0571-O", "H-0584-R",
)


def connect():
    return psycopg.connect(os.environ["DB_DSN"], row_factory=dict_row, connect_timeout=5)


def log(conn, component, level, message):
    conn.execute("INSERT INTO system_log(component,level,message) VALUES(%s,%s,%s)",
                 (component, level, message))

