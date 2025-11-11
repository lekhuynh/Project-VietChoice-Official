import pyodbc
from urllib.parse import quote_plus
from pathlib import Path
from dotenv import load_dotenv

# load .env from be/
env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(env_path)

import os

driver = os.getenv('db_driver') or 'ODBC Driver 17 for SQL Server'
server = os.getenv('db_server') or 'localhost'
db = os.getenv('db_name') or 'vietchoice'
user = os.getenv('db_user') or 'sa'
password = os.getenv('db_password') or ''

conn_str = f"DRIVER={{{driver}}};SERVER={server};DATABASE={db};UID={user};PWD={password};TrustServerCertificate=Yes"
print('Using connection string (masked):')
print(conn_str.replace(password, '***'))
try:
    cn = pyodbc.connect(conn_str, timeout=5)
    print('Connected OK')
    cn.close()
except Exception as e:
    print('Connection failed:', e)
