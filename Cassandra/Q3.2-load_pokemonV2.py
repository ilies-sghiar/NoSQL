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

# créer keyspace si besoin
session.execute(f"""
    CREATE KEYSPACE IF NOT EXISTS {KEYSPACE}
    WITH replication = {{'class': 'SimpleStrategy', 'replication_factor': '1'}}
""")

session.set_keyspace(KEYSPACE)
# créer table
session.execute(f"""
    CREATE TABLE IF NOT EXISTS {TABLE} (
        name text PRIMARY KEY,
        jname text,
        type1 text,
        type2 text,
        height double,
        weight double,
        type_efficacy map<text, text>
    )
""")

def convert_value(value):
    if isinstance(value, float):
        return float(value)
    elif isinstance(value, dict):
        # convertir chaque clé/valeur en string
        return {str(k): str(v) for k, v in value.items()}
    else:
        return str(value)
    
attributs = ["name","jname","type1","type2","height-m","weight-kg","type_efficacy"]

def clean(name: str) -> str:
    return name.split('-')[0]

def insert_row(data):
    columns = []
    placeholders = []
    values = []
    for k, v in data.items():
        if k in attributs:
            columns.append(clean(k))
            placeholders.append("%s")
            values.append(convert_value(v))
    cql = f"INSERT INTO pokemon ({', '.join(columns)}) VALUES ({', '.join(placeholders)})"
    session.execute(cql, values)


def load_pokemon_from_folder(folder_path):
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
                            insert_row(data)
                            print(f"Inserted pokemon from {filename}")
                    except json.JSONDecodeError:
                        print(f"Erreur JSON dans {filename}")


if __name__ == "__main__":
    dossier_json = "docs/json"
    load_pokemon_from_folder(dossier_json)
    