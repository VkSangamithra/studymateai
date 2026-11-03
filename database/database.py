import mysql.connector

def get_connection():

    connection = mysql.connector.connect(

        host="127.0.0.1",
        port=3307,
        user="root",
        password="ROOT",
        database="studymate_ai"

    )

    return connection