import os
import json
from cassandra.cluster import Cluster
from cassandra.query import SimpleStatement
import re
import time
import sqlite3

cluster = Cluster(['127.0.0.1'], port=9042)  
session = cluster.connect()

KEYSPACE = 'pokedex'
session.set_keyspace(KEYSPACE)

print("--------------Table Location--------------")
moyenne = 0
for i in range(10):
    start_time = time.perf_counter()
    table = "location"
    session.execute(f"SELECT * FROM {table}")
    end_time = time.perf_counter()
    elapsed = end_time - start_time
    moyenne += elapsed/10
print(f"Scan complet de la table Cassandra : En moyenne en {moyenne:.3f} secondes")

conn = sqlite3.connect("pokedex.sqlite")
cursor = conn.cursor()

moyenne = 0
for i in range(10):
    start_time = time.perf_counter()

    query = """
    select ln2.name as location_name, ln1.name as japanese_name, rn.name from locations as l join location_names as ln1 on l.id = ln1.location_id join location_names as ln2 on l.id = ln2.location_id join regions as r on l.region_id = r.id join region_names as rn on r.id = rn.region_id where ln1.local_language_id = 1 and ln2.local_language_id = 9 and rn.local_language_id=9 order by 1;
    """
    cursor.execute(query)
    cursor.fetchall()
    end_time = time.perf_counter()
    elapsed = end_time - start_time
    moyenne += elapsed/10

print(f"Scan complet de la table SQLite: En moyenne en {moyenne:.3f} secondes")

print("--------------Table Pokemon---------------")
moyenne = 0
for i in range(10):
    start_time = time.perf_counter()
    table = "pokemon"
    session.execute(f"SELECT * FROM {table}")
    end_time = time.perf_counter()
    elapsed = end_time - start_time
    moyenne += elapsed/10
print(f"Scan complet de la table Cassandra : En moyenne en {moyenne:.3f} secondes")

conn = sqlite3.connect("pokedex.sqlite")
cursor = conn.cursor()

moyenne = 0
for i in range(3):
    start_time = time.perf_counter()

    query = """
    SELECT
ps1.name AS name,
ps2.name AS jname,
height,
weight,
min(pt.type_id) AS type1,
max(pt.type_id) AS type2,
type_efficacy
FROM
pokemon AS p
LEFT JOIN pokemon_species_names AS ps1 ON p.species_id = ps1.pokemon_species_id
LEFT JOIN pokemon_species_names AS ps2 ON p.species_id = ps2.pokemon_species_id
LEFT JOIN pokemon_types AS pt ON p.id = pt.pokemon_id
LEFT JOIN (
    SELECT
        pokemon_id,
        '{' || GROUP_CONCAT('"' || target_type_id || '": ' || max_eff) || '}' AS type_efficacy
    FROM
        (
            SELECT
                pokemon_id,
                target_type_id,
                MAX(damage_factor) AS max_eff
            FROM
                (
                    SELECT
                        pm.pokemon_id,
                        t.target_type_id,
                        t.damage_factor
                    FROM
                        pokemon_moves AS pm
                        JOIN moves AS m ON pm.move_id = m.id
                        JOIN type_efficacy AS t ON m.type_id = t.damage_type_id
                    WHERE
                        pm.pokemon_id <= 151
                ) AS sub
            GROUP BY
                pokemon_id,
                target_type_id
        ) AS eff
    GROUP BY
        pokemon_id
) AS sub2 ON p.id = sub2.pokemon_id
WHERE
ps1.local_language_id = 9
AND ps2.local_language_id = 1
GROUP BY
p.id;
    """
    cursor.execute(query)
    end_time = time.perf_counter()
    elapsed = end_time - start_time
    moyenne += elapsed/3

print(f"Scan complet de la table SQLite: En moyenne en {moyenne:.3f} secondes")


"""
Résulats obtenus :

--------------Table Location--------------
Scan complet de la table Cassandra : En moyenne en 0.029 secondes
Scan complet de la table SQLite: En moyenne en 0.007 secondes
--------------Table Pokemon---------------
Scan complet de la table Cassandra : En moyenne en 0.206 secondes
Scan complet de la table SQLite: En moyenne en 6.136 secondes

"""