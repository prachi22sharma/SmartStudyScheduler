import mysql.connector
from mysql.connector import Error

def get_db_connection():
    try:
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="prachi@2204",
            database="smartstudy"
        )
        if conn.is_connected():
            return conn
        else:
            print("Connection failed!")
            return None
    except Error as e:
        print(f"Error while connecting to MySQL: {e}")
        return None