CREATE KEYSPACE IF NOT EXISTS pokedex
WITH REPLICATION = { 'class': 'SimpleStrategy', 'replication_factor': 1 };

USE pokedex;

CREATE TABLE IF NOT EXISTS pokemon_by_type (
    rang int,
    nom text,
    taille int,
    poids int,
    type text,
    PRIMARY KEY ((type), rang)
);
