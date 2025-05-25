import os
import json
from cassandra.cluster import Cluster
from cassandra.query import SimpleStatement
import re
import sqlite3
import time

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

# crée table minimaliste
session.execute(f"""
    CREATE TABLE IF NOT EXISTS {TABLE} (
        id int PRIMARY KEY
    )
""")

def infer_cassandra_type(value):
    if isinstance(value, str):
        return "text"
    elif isinstance(value, bool):
        return "boolean"
    elif isinstance(value, int):
        return "int"
    elif isinstance(value, float):
        return "double"
    elif isinstance(value, list):
        return "list<text>" 
    elif isinstance(value, dict):
        return "map<text, text>"  
    else:
        return "text"

def convert_value(value):
    if isinstance(value, dict):
        # convertir chaque clé/valeur en string
        return {str(k): str(v) for k, v in value.items()}
    elif isinstance(value, list):
        return [str(v) for v in value]
    else:
        return value

def get_existing_columns():
    query = f"SELECT column_name FROM system_schema.columns WHERE keyspace_name='{KEYSPACE}' AND table_name='{TABLE}'"
    rows = session.execute(query)
    return {row.column_name for row in rows}

def alter_table_add_column(column_name, column_type):
    print(f"Adding column {column_name} {column_type}")
    cql = f"ALTER TABLE {TABLE} ADD {column_name} {column_type}"
    session.execute(cql)

def clean(name):
    name = name.lower().strip()
    name = re.sub(r'[^a-z0-9_]', '_', name)
    if name[0].isdigit():
        name = '_' + name  
    return name


def insert_row(id, data):
    columns = ["id"]
    placeholders = ["%s"]
    values = [id]

    for k, v in data.items():
        clean_k = clean(k)  
        if clean_k != "id":
            columns.append(clean_k)
            placeholders.append("%s")
            values.append(convert_value(v))
    
    cql = f"INSERT INTO location ({', '.join(columns)}) VALUES ({', '.join(placeholders)})"
    session.execute(cql, values)

def load_locations_from_folder(folder_path):
    existing_columns = get_existing_columns()
    next_id = 1  # on incrémente manuellement l'id
    
    for filename in os.listdir(folder_path):
        if filename.endswith('.json'):
            filepath = os.path.join(folder_path, filename)
            if os.path.isfile(filepath):
                with open(filepath, 'r', encoding='utf-8') as f:
                    try:
                        data = json.load(f)
                        # verifie si c'est un document de localisation
                        if isinstance(data, dict) and "encounters" in data:
                            # ajoute les colonnes manquantes
                            for k, v in data.items():
                                k = clean(k)
                                if k not in existing_columns and k != 'id':
                                    ctype = infer_cassandra_type(v)
                                    alter_table_add_column(k, ctype)
                                    existing_columns.add(k)
                            
                            insert_row(next_id, data)
                            print(f"Inserted location id={next_id} from {filename}")
                            next_id += 1
                    except json.JSONDecodeError:
                        print(f"Erreur JSON dans {filename}")

if __name__ == "__main__":
    dossier_json = "docs/json" 
    load_locations_from_folder(dossier_json)
   