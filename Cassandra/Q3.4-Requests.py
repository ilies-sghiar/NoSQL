from cassandra.cluster import Cluster
import time
from collections import defaultdict
import ast

cluster = Cluster(['127.0.0.1'], port=9042)  

session = cluster.connect()

KEYSPACE = 'pokedex'
session.set_keyspace(KEYSPACE)

print("--------------Requête sur l'efficacité des pokemons--------------")

start_time = time.perf_counter()

# recupérer les pokemons
rows = session.execute("SELECT name, type1, type2, type_efficacy FROM pokemon")

# stocker dans une liste
pokemons = []
for row in rows:
    pokemons.append({
        'name': row.name,
        'type1': row.type1,
        'type2': row.type2,
        'type_efficacy': row.type_efficacy
    })

for attacker in pokemons:
    count_inefficace = 0
    for defender in pokemons:
        inefficace = False
        for t in [defender['type1'], defender['type2']]:
            if t:
                efficacy_str = attacker['type_efficacy'].get(t, '1')
                efficacy = float(efficacy_str)
            if efficacy == 0:
                inefficace = True
                break
        if inefficace:
            count_inefficace += 1
    #print(f"{attacker['name']} est inefficace contre {count_inefficace} pokémons")

end_time = time.perf_counter()
elapsed = end_time - start_time
print(f"Requête sur l'efficacité: En {elapsed:.3f} secondes")

print("--------------Requête sur l'étalement géographique des pokemons--------------")

start_time = time.perf_counter()
rows = session.execute("SELECT location_name, encounters, region FROM location")

region_pokemon_locations = defaultdict(lambda: defaultdict(set))  # region -> pokemon -> set(locations)
region_locations_count = defaultdict(set)  # region -> set(locations)

for row in rows:
    region = row.region
    location_name = row.location_name
    try:
        encounters = ast.literal_eval(row.encounters)  # car encounters est stocké en text dans cassandra
    except Exception as e:
        print(f"erreur de parsing")
        continue


    # pokemons uniques dans cette location (car encounters stock les infos de différentes version du jeu)
    pokemons_in_location = set()
    for group_pokemons in encounters.values():
        pokemons_in_location.update(group_pokemons)

    # memorise que cette location appartient à cette région
    region_locations_count[region].add(location_name)

    # pour chaque pokémon, memorise qu'il est dans cette location
    for p in pokemons_in_location:
        region_pokemon_locations[region][p].add(location_name)

# calcul de l'etalement
for region, pokemon_loc_map in region_pokemon_locations.items():
    total_locations = len(region_locations_count[region])
    #print(f"Region: {region} (total locations: {total_locations})")
    for p, locations_set in pokemon_loc_map.items():
        etalement = round(100.0 * len(locations_set) / total_locations, 2) if total_locations > 0 else 0
        #print(f"  {p}: {etalement}%")
    #print("-" * 40)

end_time = time.perf_counter()
elapsed = end_time - start_time
print(f"Requête sur l'etalement: En {elapsed:.3f} secondes")


"""

Comparaison des résultats :

Sur Cassandra, nous obtenons :

--------------Requête sur l'efficacité des pokemons--------------
Requête sur l'efficacité: En 1.216 secondes
--------------Requête sur l'étalement géographique des pokemons--------------
Requête sur l'etalement: En 0.022 secondes

Sur MongoDB nous obtenons :

--------------Requête sur l'efficacité des pokemons--------------
Requête sur l'efficacité: En 0.596 secondes
--------------Requête sur l'étalement géographique des pokemons--------------
Requête sur l'etalement: En 0.0518 secondes

Sur SQLite nous obtenons :

--------------Requête sur l'efficacité des pokemons--------------
Requête sur l'efficacité: En 0.034 secondes
--------------Requête sur l'étalement géographique des pokemons--------------
Requête sur l'etalement: En 0.064 secondes

Ainsi pour l'efficacité des pokemons nous avons:
SQLite > MongoDB > Cassandra

Mais pour l'étalement on a :
Cassandra > MongoDB > SQLite
"""

