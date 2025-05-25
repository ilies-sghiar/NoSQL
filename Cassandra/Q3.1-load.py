import sqlite3
from cassandra.cluster import Cluster

def copy_data_sqlite_to_cassandra(sqlite_db_path):
    # connexion a sqlite
    sqlite_conn = sqlite3.connect(sqlite_db_path)
    sqlite_cursor = sqlite_conn.cursor()

    # connexion cassandra
    cluster = Cluster(['127.0.0.1'], port=9042)

    session = cluster.connect()

    # ici on specifie le keyspace
    session.set_keyspace('pokedex')

    create_pokemon_view = """
    CREATE VIEW IF NOT EXISTS pokemon_view AS
    SELECT DISTINCT
        p.id,
        pn.name,
        p.height,
        p.weight
    FROM
        pokemon p
    JOIN
        pokemon_species_names pn ON p.species_id = pn.pokemon_species_id
    WHERE
        pn.local_language_id = 5
        AND p.id NOT IN (
            SELECT pokemon_id FROM pokemon_forms WHERE is_mega = 1
        );
    """

    create_pokemon_types_view = """
    CREATE VIEW IF NOT EXISTS pokemon_types_view AS
    SELECT
        pt.pokemon_id,
        tn.name AS type_name
    FROM
        pokemon_types pt
    JOIN
        type_names tn ON pt.type_id = tn.type_id
    WHERE
        tn.local_language_id = 5
        AND pt.pokemon_id NOT IN (
            SELECT pokemon_id FROM pokemon_forms WHERE is_mega = 1
        );
    """

    sqlite_cursor.execute(create_pokemon_view)
    sqlite_cursor.execute(create_pokemon_types_view)
    sqlite_conn.commit()

    # requête pour joindre les deux vues
    join_query = """
    SELECT
        pv.id AS rang,
        pv.name AS nom,
        pv.height AS taille,
        pv.weight AS poids,
        ptv.type_name as type
    FROM
        pokemon_view pv
    JOIN
        pokemon_types_view ptv ON pv.id = ptv.pokemon_id;
    """

    sqlite_cursor.execute(join_query)

    # insérer dans Cassandra
    insert_query = """
    INSERT INTO pokemon_by_type (
        rang, nom, taille, poids, type
    ) VALUES (%s, %s, %s, %s, %s)
    """

    for row in sqlite_cursor.fetchall():
        session.execute(insert_query, row)

    print("Données copiées de SQLite vers Cassandra")

    # ferme connexions
    sqlite_conn.close()
    cluster.shutdown()

copy_data_sqlite_to_cassandra("pokedex.sqlite")
