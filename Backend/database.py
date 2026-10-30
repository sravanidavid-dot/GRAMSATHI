import mysql.connector
from mysql.connector import Error
from config import DB_CONFIG


def get_db_connection():

    try:

        connection = mysql.connector.connect(
            host=DB_CONFIG["host"],
            user=DB_CONFIG["user"],
            password=DB_CONFIG["password"],
            database=DB_CONFIG["database"]
        )

        if connection.is_connected():

            # Use Indian Standard Time for this DB session
            cursor = connection.cursor()

            cursor.execute(
                "SET time_zone = '+05:30'"
            )

            cursor.close()

            return connection

    except Error as e:

        print(
            "MySQL connection error:",
            e
        )

        return None