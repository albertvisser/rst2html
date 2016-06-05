# set up database

CREATE DATABASE rst2html;
CREATE TABLE sites (
    id serial PRIMARY KEY,
    name    VARCHAR UNIQUE
    );
CREATE TABLE site_settings (
    id serial   PRIMARY KEY,
    site_id     INTEGER REFERENCES sites,
    settname VARCHAR,
    settval     VARCHAR
    );
CREATE TABLE directories (
    id serial   PRIMARY KEY,
    site_id     INTEGER REFERENCES sites,
    dirname  VARCHAR
    );
CREATE TABLE doc_stats (
    id serial               PRIMARY KEY,
    dir_id                  INTEGER REFERENCES directories,
    docname            VARCHAR,
    source_docid       INTEGER,   /* references TABLES[4] */
    source_updated  TIMESTAMP,
    target_docid        INTEGER, /* references TABLES[4] */
    target_updated   TIMESTAMP,
    mirror_updated   TIMESTAMP
    );
CREATE TABLE documents (
    id serial     PRIMARY KEY,
    name        VARCHAR,
    previous    VARCHAR,
    currtext    VARCHAR
    );
