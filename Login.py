import hashlib
import mysql.connector as db
from getpass import getpass
import asyncio
from concurrent.futures import ThreadPoolExecutor

async def hash_password(password):
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _hash_password_sync, password)

def _hash_password_sync(password):
    hash_object = hashlib.sha256()
    hash_object.update(password.encode('utf-8'))
    return hash_object.hexdigest()

def create_connection():
    try:
        conn = db.connect(
            host="127.0.0.1",
            port="2406",
            user="root",
            password="root",
            database="login_db",
            auth_plugin='mysql_native_password'
        )
        return conn
    except db.Error as err:
        print(err)
    return None

def create_table(conn):
    create_tb = """
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(50) NOT NULL UNIQUE,
            password VARCHAR(64) NOT NULL
        )
    """
    try:
        cursor = conn.cursor()
        cursor.execute(create_tb)
        cursor.close() 
    except db.Error as err:
        print(err)

async def register(conn, username, password):
    hashed_password = await hash_password(password)
    sql = "INSERT INTO users (username, password) VALUES (%s, %s)"
    try:
        cursor = conn.cursor()
        cursor.execute(sql, (username, hashed_password))
        conn.commit()
        cursor.close() 
        print(f"'{username}' has been registered.")
    except db.Error as err:
        print(err)

async def login(conn, username, password):
    sql = "SELECT password FROM users WHERE username = %s"
    try:
        cursor = conn.cursor()
        cursor.execute(sql, (username,))
        result = cursor.fetchone()
        cursor.close() 
        if result:
            hashed_password = result[0]
            if await hash_password(password) == hashed_password:
                print("You have been logged in.")
            else:
                print("Incorrect password.")
        else:
            print("User not found.")
    except db.Error as err:
        print(err)

async def main():
    conn = create_connection()
    if conn is not None:
        create_table(conn)

        print("\n1. Register")
        print("\n2. Login")
        choice = input("Choice: ")

        if choice == '1':
            username = input("Username: ")
            password = getpass("Password: ")
            await register(conn, username, password)

        elif choice == '2':
            username = input("Username: ")
            password = getpass("Password: ")
            await login(conn, username, password)

        else:
            print("Invalid choice.")

        conn.close()
    else:
        print("Error! Failed to connect.")

if __name__ == '__main__':
    asyncio.run(main())
