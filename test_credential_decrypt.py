import psycopg2
from psycopg2.extras import RealDictCursor
import json

conn = psycopg2.connect(
    host='localhost',
    port=5432,
    database='optiinfra',
    user='optiinfra',
    password='optiinfra'
)

cur = conn.cursor(cursor_factory=RealDictCursor)
cur.execute("""
    SELECT decrypt_credential(encrypted_credentials, 'optiinfra_dev_key_change_in_production') as credentials 
    FROM cloud_credentials 
    WHERE credential_name = 'Production Vultr'
""")

result = cur.fetchone()
print(f"Type: {type(result['credentials'])}")
print(f"Value: {result['credentials']}")
print(f"Repr: {repr(result['credentials'])}")

if isinstance(result['credentials'], str):
    print("It's a string! Parsing...")
    creds = json.loads(result['credentials'])
    print(f"Parsed type: {type(creds)}")
    print(f"API Key: {creds.get('api_key')}")
elif isinstance(result['credentials'], dict):
    print(f"It's already a dict!")
    print(f"API Key: {result['credentials'].get('api_key')}")
else:
    print(f"Unknown type!")

conn.close()
