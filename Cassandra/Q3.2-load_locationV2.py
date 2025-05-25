import os
import json
from cassandra.cluster import Cluster
from cassandra.query import SimpleStatement
import re
import time
import sqlite3


KEYSPACE = 'pokedex'
TABLE = 'location'

# connexion Cassandra
cluster = Cluster(['127.0.0.1'], port=9042) 
session = cluster.connect()

# crée keyspace si besoin
session.execute(f"""
    CREATE KEYSPACE IF NOT EXISTS {KEYSPACE}
    WITH replication = {{'class': 'SimpleStrategy', 'replication_factor': '1'}}
""")

session.set_keyspace(KEYSPACE)
# crée table
session.execute(f"""
    CREATE TABLE IF NOT EXISTS {TABLE} (
        location_name text PRIMARY KEY,
        japanese_name text,
        region text,
        encounters text
    )
""")

# j'ai décidé d'ajouté encounters car nécessaire pour calculer l'étalement géographique des pokémons(voir Q3.4).

def convert_value(value):
    return str(value)
    
attributs = ["location_name","japanese_name","region","encounters"]


def insert_row(data):
    columns = []
    placeholders = []
    values = []
    for k, v in data.items():
        if k in attributs:
            columns.append(k)
            placeholders.append("%s")
            values.append(convert_value(v))
    if "location_name" in columns:
        cql = f"INSERT INTO location ({', '.join(columns)}) VALUES ({', '.join(placeholders)})"
        session.execute(cql, values)


def load_location_from_folder(folder_path):
    for filename in os.listdir(folder_path):
        if filename.endswith('.json'):
            filepath = os.path.join(folder_path, filename)
            if os.path.isfile(filepath):
                with open(filepath, 'r', encoding='utf-8') as f:
                    try:
                        data = json.load(f)
                        # verifie si c'est un document de location
                        if isinstance(data, dict) and "encounters" in data and data:
                            #print("NOW IN ", filename)
                            insert_row(data)
                            print(f"Inserted location from {filename}")
                    except json.JSONDecodeError:
                        print(f"Erreur JSON dans {filename}")


if __name__ == "__main__":
    dossier_json = "docs/json"  
    load_location_from_folder(dossier_json)
    