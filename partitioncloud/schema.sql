DROP TABLE IF EXISTS user;
DROP TABLE IF EXISTS partition;
DROP TABLE IF EXISTS album;
DROP TABLE IF EXISTS contient_partition;
DROP TABLE IF EXISTS contient_user;
DROP TABLE IF EXISTS search_results;

CREATE TABLE user (
	id INTEGER PRIMARY KEY AUTOINCREMENT,
	username TEXT UNIQUE NOT NULL,
	password TEXT NOT NULL,
	access_level INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE partition (
	uuid TEXT(36) PRIMARY KEY,
	name TEXT NOT NULL,
	author TEXT,
	body TEXT
);

CREATE TABLE album (
	id INTEGER PRIMARY KEY,
	name TEXT NOT NULL,
	uuid TEXT(36) UNIQUE NOT NULL
);

CREATE TABLE contient_partition (
	partition_uuid TEXT(36) NOT NULL,
	album_id INTEGER NOT NULL,
	PRIMARY KEY (partition_uuid, album_id)
);

CREATE TABLE contient_user (
	user_id INTEGER NOT NULL,
	album_id INTEGER NOT NULL,
	PRIMARY KEY (user_id, album_id)
);

CREATE TABLE search_results (
	uuid TEXT(36) PRIMARY KEY,
	url TEXT,
	creation_time TEXT NULL DEFAULT (datetime('now', 'localtime'))
);