Dans ce dossier vous trouverez les fichiers suivants :

- data.cql : spécifie la table Pokémon ⋈ PokémonType dans le langage CQL sous le nom de table pokemon_by_type
- Q3.1-load.py : pour remplir la table pokemon_by_type
- Q3.2-load_locationV2.py : pour stocker la table "location", avec les champs "location_name", "japanese_name" et "region" (suite au mail)
- Q3.2-load_pokemonV2.py : pour stocker la table "pokemon", avec les champs "name", "jname", "type1", "type2", "height-m", "weight-kg" et "type_efficacy". (suite au mail)
- Q3.3-CompareExecutionTimes.py : compare les temps de scan de SQLite et Cassandra
- Q3.4-Requests.py : pour effectuer une requête d'étalement géographique et une autre d'efficacité par pokémon et comparer les résultats entre SQLite, Cassandra et MongoDB
- load_locationV1.py : Ancienne version de Q3.2-load_locationV2.py (avant le mail), mais plus flexible
- load_locationV2.py : Ancienne version de Q3.2-load_pokemonV2.py (avant le mail), mais plus flexible 

Avant d'éxécuter les codes:

docker pull cassandra:latest

docker network create cassandra

docker run --rm -d --name cassandra --hostname cassandra --network cassandra cassandra

docker cp data.cql cassandra:/data.cql

docker exec -it cassandra cqlsh -f /data.cql

Puis éxécuter les codes dans l'ordre suivant :

- Q3.1-load.py 
- Q3.2-load_locationV2.py 
- Q3.2-load_pokemonV2.py 
- Q3.3-CompareExecutionTimes.py
- Q3.4-Requests.py