import psycopg2
from psycopg2.extras import RealDictCursor
from time import sleep
from os import environ
from dotenv import load_dotenv

load_dotenv()


def db_open():
    while True:
        try:
            con = psycopg2.connect(database=environ["POSTGRES_DB"],
                                   user=environ["POSTGRES_USER"],
                                   password=environ["POSTGRES_PASSWORD"],
                                   host=environ["HOST"],
                                   port=environ["PORT_DB"],
                                   cursor_factory=RealDictCursor)
            cur = con.cursor()
            print('successuly connected')
            return con, cur
        except Exception as p:
            print('fail to connect to database')
            print(f'Error: {p}')
            sleep(1)


def db_close(con):
    con.commit()
    con.close()
