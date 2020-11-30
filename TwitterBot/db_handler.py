from sqlalchemy import create_engine
from sqlalchemy import (
    Table, Column, Integer, String, Boolean, MetaData,
    ForeignKey, DateTime, BigInteger,
)
import datetime

# Global Variables
SQLITE = 'sqlite'

# Table Names
LOGIN_ACTIVITY = 'loginActivity'  # logs the login activity
NOTIFICATIONS = 'notifications'  # table to handle notifications & statuses


class Database:
    DB_ENGINE = {
        SQLITE: 'sqlite:///{DB}'
    }
    db_engine = None  # Main DB Connection Ref Obj

    def __init__(self, dbtype, username='', password='', dbname=''):
        dbtype = dbtype.lower()

        if dbtype in self.DB_ENGINE.keys():
            engine_url = self.DB_ENGINE[dbtype].format(DB=dbname)
            self.db_engine = create_engine(engine_url)
            print(self.db_engine)
        else:
            print("DBType is not found in DB_ENGINE")

    @staticmethod
    def __get_timestamp():
        return datetime.datetime.today().strftime("%m-%d-%Y %H:%M:%S")

    def create_db_tables(self):
        metadata = MetaData()

        login_activity = Table(LOGIN_ACTIVITY, metadata,
                               Column('id',
                                      BigInteger().with_variant(Integer, 'sqlite'),
                                      primary_key=True),
                               Column('username', String),
                               Column('login_succeeded', Boolean),
                               Column('timestamp', DateTime),
                               )
        notifications = Table(NOTIFICATIONS, metadata,
                              Column('id',
                                     BigInteger().with_variant(Integer, 'sqlite'),
                                     primary_key=True),
                              Column('tweet_id', String),
                              Column('sender', String),
                              Column('text', String),
                              Column('request_type', String),
                              Column('response_status', String),
                              Column('timestamp', DateTime),
                              )
        try:
            metadata.create_all(self.db_engine)
            print("Tables created")
        except Exception as e:
            print("Error occurred during Table creation!")
            print(e)

    def execute_query(self, query=None):
        if query is None: return
        print(query)

        with self.db_engine.connect() as connection:
            try:
                connection.execute(query)
            except Exception as e:
                print(e)

    def print_all_data(self, table=None, query=None, get_results=False):
        query = query \
            if query is not None \
            else f"SELECT * FROM '{table}';"
        print(query)

        with self.db_engine.connect() as connection:
            try:
                result = connection.execute(query)
            except Exception as e:
                print(e)
            else:
                rows = []
                for row in result:
                    print(row)
                    rows.append(row)

                result.close()
                print("\n")

                if get_results: return rows

    def insert_login_activity(self, username, login_succeeded):
        query = f"INSERT INTO {LOGIN_ACTIVITY}" \
                f"(id, username, login_succeeded, timestamp) " \
                f"VALUES (NULL, '{username}', " \
                f"{login_succeeded}, datetime('now', 'localtime'));"

        self.execute_query(query)
        self.print_all_data(LOGIN_ACTIVITY)

    def query_notification_for_tweet_id(self, tweet_id):
        query = f"SELECT * FROM {NOTIFICATIONS} " \
                f"WHERE tweet_id='{tweet_id}';"
        results = self.print_all_data(query=query, get_results=True)
        results_count = len(results)
        print(results)
        print(f"Results found: {results_count}")

        if results_count > 0:
            is_queued = False \
                if results[0]['response_status'] == 'DONE' \
                else True

            return True, is_queued

        return False, None

    def insert_notification(self, tweet):
        response_status = "DONE" if not tweet.is_queued else "Queued"
        print(f"Inserting new Tweet")
        query = f"INSERT INTO {NOTIFICATIONS} " \
                f"(id, tweet_id, sender, text, request_type, " \
                f"response_status, timestamp) " \
                f"VALUES (NULL, '{tweet.id}', '{tweet.sender}', " \
                f"'{tweet.text}', '{tweet.command_found}', " \
                f"'{response_status}', datetime('now', 'localtime'));"

        self.execute_query(query)
        self.print_all_data(LOGIN_ACTIVITY)

    def update_notification_is_done(self, tweet_id):
        query = f"UPDATE {NOTIFICATIONS} " \
                f"set response_status='DONE' " \
                f"WHERE tweet_id='{tweet_id}';"
        self.execute_query(query)
        print(self.print_all_data(NOTIFICATIONS))
