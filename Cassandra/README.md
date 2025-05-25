Dans ce dossier, vous trouverez les fichiers suivants :

- **data.cql** : définit la table Pokémon ⋈ PokémonType en CQL sous le nom **pokemon_by_type**
- **Q3.1-load.py** : script pour remplir la table **pokemon_by_type**
- **Q3.2-load_locationV2.py** : script pour insérer les données dans la table **location** avec les champs *location_name*, *japanese_name* et *region* (conforme aux dernières consignes du mail)
- **Q3.2-load_pokemonV2.py** : script pour insérer les données dans la table **pokemon**, avec les champs *name*, *jname*, *type1*, *type2*, *height-m*, *weight-kg* et *type_efficacy* (conforme aux dernières consignes du mail)
- **Q3.3-CompareExecutionTimes.py** : compare les temps de scan entre SQLite et Cassandra
- **Q3.4-Requests.py** : exécute des requêtes d’étalement géographique et d’efficacité par Pokémon, puis compare les résultats entre SQLite, Cassandra et MongoDB
- **load_locationV1.py** : ancienne version de Q3.2-load_locationV2.py (avant mise à jour par mail), plus flexible
- **load_locationV2.py** : ancienne version de Q3.2-load_pokemonV2.py (avant mise à jour par mail), plus flexible

---

### Instructions avant exécution des scripts :

```bash
docker pull cassandra:latest

docker network create cassandra

docker run --rm -d --name cassandra --hostname cassandra --network cassandra cassandra

docker cp data.cql cassandra:/data.cql

docker exec -it cassandra cqlsh -f /data.cql

Ordre recommandé d’exécution des scripts :

Q3.1-load.py

Q3.2-load_locationV2.py

Q3.2-load_pokemonV2.py

Q3.3-CompareExecutionTimes.py

Q3.4-Requests.py

<p align="center"> <img src="Cassandra/logo.png" alt="Cassandra Logo" width="200" /> </p>