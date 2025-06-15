
import os
import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv

load_dotenv()

def get_db_connection():
    try:
        conn = mysql.connector.connect(
            host=os.environ.get("DB_HOST"),
            user=os.environ.get("DB_USER"),
            password=os.environ.get("DB_PASSWORD"),
            database=os.environ.get("DB_NAME")
        )
        if conn.is_connected():
            return conn
        else:
            print("Connection failed!")
            return None
    except Error as e:
        print(f"Error while connecting to MySQL: {e}")
        return None