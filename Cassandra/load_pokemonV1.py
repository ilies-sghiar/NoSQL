import os
import json
from cassandra.cluster import Cluster
from cassandra.query import SimpleStatement
import re
import time
import sqlite3


KEYSPACE = 'pokedex'
TABLE = 'pokemon'

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
        ndex double PRIMARY KEY,
        type_efficacy map<text, text>
    )
""")

def convert_value(value):
    if isinstance(value, dict):
        # Convertir chaque clé/valeur en string
        return {str(k): str(v) for k, v in value.items()}
    else:
        return str(value)

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
        name = 'p_' + name 
    return name

def insert_row(data):
    columns = []
    placeholders = []
    values = []

    for k, v in data.items():
        clean_k = clean(k)
        columns.append(clean_k)
        placeholders.append("%s")
        if k == "ndex":
            values.append(float(v))
        else:
            values.append(convert_value(v))
    cql = f"INSERT INTO pokemon ({', '.join(columns)}) VALUES ({', '.join(placeholders)})"
    session.execute(cql, values)



def load_pokemon_from_folder(folder_path):
    existing_columns = get_existing_columns()    
    for filename in os.listdir(folder_path):
        if filename.endswith('.json'):
            filepath = os.path.join(folder_path, filename)
            if os.path.isfile(filepath):
                with open(filepath, 'r', encoding='utf-8') as f:
                    try:
                        data = json.load(f)
                        # verifie si c'est un document de pokemon
                        if isinstance(data, dict) and "encounters" not in data and data:
                            #print("NOW IN ", filename)
                            # ajoute colonnes manquantes
                            for k, v in data.items():
                                k = clean(k)
                                if k not in existing_columns:
                                    ctype = "text"
                                    alter_table_add_column(k, ctype)
                                    existing_columns.add(k)
                            
                            insert_row(data)
                            print(f"Inserted pokemon from {filename}")
                    except json.JSONDecodeError:
                        print(f"Erreur JSON dans {filename}")


if __name__ == "__main__":
    dossier_json = "docs/json"  
    load_pokemon_from_folder(dossier_json)
    