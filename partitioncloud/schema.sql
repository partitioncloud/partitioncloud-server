DROP TABLE IF EXISTS user;
DROP TABLE IF EXISTS partition;
DROP TABLE IF EXISTS album;
DROP TABLE IF EXISTS contient_partition;
DROP TABLE IF EXISTS contient_user;
DROP TABLE IF EXISTS search_results;
DROP TABLE IF EXISTS groupe;
DROP TABLE IF EXISTS groupe_contient_user;
DROP TABLE IF EXISTS groupe_contient_album;
DROP TABLE IF EXISTS attachments;

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
	body TEXT,
	user_id INTEGER,
	source TEXT DEFAULT 'unknown'
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

CREATE TABLE groupe (
	id INTEGER PRIMARY KEY,
	name TEXT NOT NULL,
	uuid TEXT(36) NOT NULL
);

CREATE TABLE groupe_contient_user (
	groupe_id INTEGER NOT NULL,
	user_id INTEGER NOT NULL,
	is_admin INTEGER NOT NULL DEFAULT 0,
	PRIMARY KEY (groupe_id, user_id)
);

CREATE TABLE groupe_contient_album (
	groupe_id INTEGER NOT NULL,
	album_id INTEGER NOT NULL,
	PRIMARY KEY (groupe_id, album_id)
);

CREATE TABLE attachments (
	uuid TEXT(36) PRIMARY KEY,
	name TEXT NOT NULL,
	filetype TEXT NOT NULL DEFAULT 'mp3',
	partition_uuid INTEGER NOT NULL,
	user_id INTEGER NOT NULL
);