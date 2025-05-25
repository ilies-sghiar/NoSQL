# MOGODB
# Adam NHAILA et Iliès SGHIAR

from pymongo import MongoClient
import time


#question 1:

# Les documents ont été insérés dans la collection pokedex de la base de données pokedex_db.

# Un meilleur choix de clé serait le champ "name" (nom du Pokémon ou de la localité), car il est unique, lisible et facilite la recherche directe d’un document.

# question 2
client = MongoClient()
db = client.pokedex_db

fire_pokemons = db.pokedex.find({
    "$and": [
        {
            "$or": [
                { "type1": "Fire" },
                { "type2": "Fire" }
            ]
        },
        {
            "weight-kg": { "$lt": 100 }
        }
    ]
})

# Affiche les résultats
for p in fire_pokemons:
    print(p["name"], "-", p["weight-kg"], "kg")



#question 3 mettre à jour les documents; ajout du type

# le critère pour les pokemon c'est name est type1 et pour lcoalisation c'est encounters , l'un n'existe pas dans l'autre d

pokemon=db.pokedex.update_many(
    {"weight-kg":{"$exists":True}, "type1":{"$exists":True}},
    {"$set": {"typed": "pokemon"}}
    )

localisation=db.pokedex.update_many(
    {"encounters":{"$exists": True}},
    {"$set": {"typed":"localisation"}}
)

print(f"Documents mis à jour comme Pokémon : {pokemon.modified_count}")
print(f"Documents mis à jour comme Localisation : {localisation.modified_count}")


# question 4 

# Poids incohérent : 1 kg = 2.20462 lbs (on tolère une petite marge)
TOLERANCE = 0.2  # marge de tolérance sur la conversion


resultats= db.pokedex.find({
    "typed":"pokemon",
    "$or":[
        { "name":{"$exists": False}},
        { "forme": { "$exists": False } },
        { "type1": { "$exists": False } },
        { "type2": { "$exists": False } },
        { "generation": { "$exists": False } }
        ,        
        {
            "$expr": {
                "$and": [
                    { "$gt": ["$weight-kg", 0] },
                    { "$gt": ["$weight-lbs", 0] },
                    {
                        "$gt": [
                            { "$abs": { "$subtract": [
                                "$weight-lbs",
                                { "$multiply": ["$weight-kg", 2.20462] }
                            ]}},
                            TOLERANCE
                        ]
                    }
                ]
            }
        }
    ]

})


# Affichage des résultats
for doc in resultats:
    print(doc.get("name"), "-", doc.get("weight-kg"), "kg /", doc.get("weight-lbs"), "lbs")

# Partie 2

# question 2.1:

start = time.time()

pipeline = [
    # On sélectionne uniquement les documents de type "localisation" qui possèdent les champs "encounters" et "region"
    {
        "$match": {
            "typed": "localisation",
            "encounters": {"$exists": True},
            "region": {"$exists": True}
        }
    },
    # On extrait les pokémons rencontrés dans chaque localisation, en les fusionnant en une seule liste unique
    {
        "$project": {
            "region": 1,
            "name": 1,
            "unique_pokemons": {
                "$setUnion": {
                    "$reduce": {
                        "input": {"$objectToArray": "$encounters"},
                        "initialValue": [],
                        "in": {"$concatArrays": ["$$value", "$$this.v"]}
                    }
                }
            }
        }
    },
    # Chaque pokémon est traité individuellement, un document par pokémon et localisation
    {
        "$unwind": "$unique_pokemons"
    },
    # On regroupe par pokémon et région, tout en collectant les noms uniques des localisations
    {
        "$group": {
            "_id": {
                "pokemon": "$unique_pokemons",
                "region": "$region"
            },
            "unique_locations": {"$addToSet": "$name"}
        }
    },
    # On ajoute le nombre de localisations distinctes dans lesquelles chaque pokémon apparaît
    {
        "$addFields": {
            "count_locations": {"$size": "$unique_locations"}
        }
    },
    # On regroupe par région, en rassemblant les données pour chaque pokémon et en additionnant les comptes
    {
        "$group": {
            "_id": "$_id.region",
            "pokemon_data": {
                "$push": {
                    "pokemon": "$_id.pokemon",
                    "count_locations": "$count_locations"
                }
            },
            "total_locations": {"$sum": "$count_locations"}
        }
    },
    # On récupère pour chaque région le nombre réel de localisations uniques à partir des documents sources
    {
        "$lookup": {
            "from": "pokedex",
            "let": {"region": "$_id"},
            "pipeline": [
                {
                    "$match": {
                        "typed": "localisation",
                        "$expr": {"$eq": ["$region", "$$region"]},
                        "name": {"$exists": True}
                    }
                },
                {
                    "$group": {
                        "_id": "$region",
                        "all_locations": {"$addToSet": "$name"}
                    }
                },
                {
                    "$project": {
                        "total_locations": {"$size": "$all_locations"}
                    }
                }
            ],
            "as": "region_info"
        }
    },
    # On extrait les informations de la région obtenues via le lookup
    {
        "$unwind": "$region_info"
    },
    # On déplie chaque entrée de pokémon pour effectuer les calculs finaux
    {
        "$unwind": "$pokemon_data"
    },
    # On calcule l’étalement de chaque pokémon, c’est-à-dire la proportion de lieux où il est présent par rapport au total des lieux de la région
    {
        "$project": {
            "region": "$_id",
            "pokemon": "$pokemon_data.pokemon",
            "count_locations": "$pokemon_data.count_locations",
            "total_locations": "$region_info.total_locations",
            "etalement": {
                "$cond": [
                    {"$gt": ["$region_info.total_locations", 0]},
                    {
                        "$round": [
                            {
                                "$multiply": [
                                    {"$divide": ["$pokemon_data.count_locations", "$region_info.total_locations"]},
                                    100
                                ]
                            },
                            2
                        ]
                    },
                    0
                ]
            }
        }
    },
    # On trie les résultats par nom de pokémon et par région pour une lecture plus claire
    {
        "$sort": {
            "pokemon": 1,
            "region": 1
        }
    }
]

results = db.pokedex.aggregate(pipeline)

# Affichage des résultats avec pourcentage d’étalement pour chaque pokémon dans chaque région
for doc in results:
    print(f"Pokémon : {doc['pokemon']} - Région : {doc['region']} - Étalement : {doc['etalement']}%")

end = time.time()
print(f"\n Temps d'exécution MongoDB : {end - start:.4f} secondes")

#  output: Temps d'exécution MongoDB : 0.0518 secondes
#  sql: temps d'execution 64ms
#  donc à peu près similaire; on a une différence de 0.01 miliseconde.
#question 2

import time

start_time = time.time()

results = db.pokedex.aggregate([
    {
        "$match": {
            "typed": "pokemon",
            "type1": { "$exists": True },
            "type_efficacy": { "$exists": True },
            "generation": 1.0 
        }
    },
    {
        "$lookup": {
            "from": "pokedex",
            "let": {
                "attacker_type1": "$type1",
                "attacker_type2": "$type2"
            },
            "pipeline": [
                {
                    "$match": {
                        "typed": "pokemon",
                        "type_efficacy": { "$exists": True }
                    }
                },
                {
                    "$addFields": {
                        "eff_array": { "$objectToArray": "$type_efficacy" }
                    }
                },
                {
                    "$match": {
                        "$expr": {
                            "$or": [
                                {
                                    "$in": [
                                        { "k": "$$attacker_type1", "v": 0 },
                                        "$eff_array"
                                    ]
                                },
                                {
                                    "$in": [
                                        { "k": "$$attacker_type2", "v": 0 },
                                        "$eff_array"
                                    ]
                                }
                            ]
                        }
                    }
                }
            ],
            "as": "immune"
        }
    },
    {
        "$match": {
            "immune.0": { "$exists": True }
        }
    },
    {
        "$project": {
            "name": 1,
            "immune.name": 1,
            "immune_count": { "$size": "$immune" }
        }
    }
])

for doc in results:
    exemples = ", ".join([p["name"] for p in doc["immune"][:3]])
    print(f"{doc['name']} est inefficace contre {doc['immune_count']} Pokémon (ex: {exemples})")

end_time = time.time()
print(f"\n Temps d'exécution MongoDB : {end_time - start_time:.3f} secondes")

# output:  Temps d'exécution MongoDB : 0.596 secondes
# sql  in 34ms
# On a une difference de 0.026s


# question 3 

# fonction pour distribution regionale:

import time
from collections import defaultdict

from collections import defaultdict
import time

def find_pokemon_distribution(docs):
    start = time.time()

    total_locations_per_region = defaultdict(set)
    pokemon_locations_per_region = defaultdict(set)

    for loc in docs:
        if loc.get("typed") != "localisation" or "encounters" not in loc or "region" not in loc:
            continue

        region = loc["region"]
        location_id = loc.get("name")

        # Ajoute la localisation à la région
        total_locations_per_region[region].add(location_id)

        # Liste unique de Pokémon rencontrés dans ce lieu
        seen_pokemons = set()
        for encounter_list in loc["encounters"].values():
            seen_pokemons.update(encounter_list)

        for pokemon in seen_pokemons:
            pokemon_locations_per_region[(pokemon, region)].add(location_id)

    results = []
    for (pokemon, region), locations in pokemon_locations_per_region.items():
        total_locs = len(total_locations_per_region[region])
        percentage = round(len(locations) * 100.0 / total_locs, 2) if total_locs > 0 else 0.0
        results.append({
            "pokemon": pokemon,
            "region": region,
            "etalement": percentage
        })

    # Tri par Pokémon, puis par région
    results.sort(key=lambda x: (x["pokemon"], x["region"]))

    for res in results:
        print(f"Pokémon : {res['pokemon']} - Région : {res['region']} - Étalement : {res['etalement']}%")

    end = time.time()
    print(f"\n Temps d'exécution Python (répartition) : {end - start:.4f} secondes")
    return results

# fonction pour efficacité type: 

def find_type_efficacy_0(pokedex_docs):
    start = time.time()

    pokemons = [doc for doc in pokedex_docs if doc.get("typed") == "pokemon" and "type1" in doc and "type_efficacy" in doc and doc.get("generation") == 1.0]

    for attacker in pokemons:
        attacker_type1 = attacker.get("type1")
        attacker_type2 = attacker.get("type2")
        immune_targets = []

        for defender in pokemons:
            efficacy = defender.get("type_efficacy", {})
            if (attacker_type1 in efficacy and efficacy[attacker_type1] == 0) or \
               (attacker_type2 in efficacy and efficacy[attacker_type2] == 0):
                immune_targets.append(defender)

        if immune_targets:
            exemples = ", ".join([p["name"] for p in immune_targets[:3]])
            print(f"{attacker['name']} est inefficace contre {len(immune_targets)} Pokémon (ex: {exemples})")

    end = time.time()
    print(f"\n Temps d'exécution Python (type efficacy) : {end - start:.3f} secondes")


# Utilisation:

pokedex_docs = list(db.pokedex.find({}))  # on charge tout en mémoire
docs = list(db.pokedex.find({ "typed": "localisation", "encounters": { "$exists": True }, "region": { "$exists": True } }))
find_pokemon_distribution(docs)
find_type_efficacy_0(pokedex_docs)


# output: Temps d'exécution Python (répartition) : 0.0042 secondes
# output: Temps d'exécution Python (type efficacy) : 0.007 secondes
# Oui elle sont plus rapides que les pipelines équivalents

# question 4:

# Bigtable ne supporte pas la recherche textuelle nativement comme MongoDB.
# Pour reproduire $search, on doit construire un index inversé externe (ex: Elasticsearch).
# Une autre option est de stocker un index inversé manuellement dans Bigtable, ligne = mot.
# On effectue ensuite une recherche par mot-clé en consultant cet index pour retrouver les documents. 
