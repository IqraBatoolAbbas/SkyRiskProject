
import getpass
import psycopg

password = getpass.getpass("Enter skyrisk role password: ")

try:
    with psycopg.connect(
        host="localhost",
        port=5432,
        dbname="skyrisk",
        user="skyrisk",
        password=password,
        connect_timeout=5,
    ) as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT current_database(), current_user, inet_server_port()"
            )
            database, role, port = cur.fetchone()

    print("\nSUCCESS: Database connection established!")
    print(f"Database: {database}")
    print(f"Login role: {role}")
    print(f"Port: {port}")
    print("No tables or records were changed.")

except psycopg.OperationalError as error:
    print("\nCONNECTION FAILED.")
    print("Error:", str(error).splitlines()[0])

import getpass
import psycopg

password = getpass.getpass("Enter skyrisk role password: ")

try:
    with psycopg.connect(
        host="localhost",
        port=5432,
        dbname="skyrisk",
        user="skyrisk",
        password=password,
        connect_timeout=5,
    ) as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT current_database(), current_user, inet_server_port()"
            )
            database, role, port = cur.fetchone()

    print("\nSUCCESS: Database connection established!")
    print(f"Database: {database}")
    print(f"Login role: {role}")
    print(f"Port: {port}")
    print("No tables or records were changed.")

except psycopg.OperationalError as error:
    print("\nCONNECTION FAILED.")
    print("Error:", str(error).splitlines()[0])
