-- set up database

CREATE DATABASE rst2html;
\connect rst2html;
DROP TABLE sites CASCADE;
CREATE TABLE sites (
    id serial PRIMARY KEY,
    sitename    VARCHAR UNIQUE
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
    source_deleted  BOOLEAN,
    target_docid        INTEGER, /* references TABLES[4] */
    target_updated   TIMESTAMP,
    target_deleted   BOOLEAN,
    mirror_updated   TIMESTAMP
    );
CREATE TABLE documents (
    id serial     PRIMARY KEY,
    name        VARCHAR,
    previous    VARCHAR,
    currtext    VARCHAR
    );
