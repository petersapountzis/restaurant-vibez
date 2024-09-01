import pandas as pd
import pymysql

class DBmanager:
    def __init__(self):
        self.conn = pymysql.connect(
            host = "vibez-database1-instance-1.c74gs48gc437.us-east-1.rds.amazonaws.com",
            port=3306,
            user="admin",
            password="Banker2b!",
            database="restaurants"
        )
        self.cursor = self.conn.cursor()
        # set isolation level to read committed
        self.cursor.execute("SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED")
        self.conn.commit()
    def __del__(self):
        self.close()
        print("Connection closed")

    def close(self):
        """Close the database connection."""
        self.cursor.close()
        self.conn.close()

    def load_all_restaurants(self):
        """Retrieve all trades from the database."""
        self.cursor.execute("SELECT * FROM restaurant_info")
        rows = self.cursor.fetchall()
        return rows