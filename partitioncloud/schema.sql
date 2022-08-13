DROP TABLE IF EXISTS user;
DROP TABLE IF EXISTS partition;
DROP TABLE IF EXISTS album;
DROP TABLE IF EXISTS contient_partition;
DROP TABLE IF EXISTS contient_user;

CREATE TABLE user (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  username TEXT UNIQUE NOT NULL,
  password TEXT NOT NULL,
	access_level INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE partition (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,
	author TEXT,
	body TEXT
);

CREATE TABLE album (
	id INTEGER PRIMARY KEY AUTOINCREMENT,
	name TEXT NOT NULL
);

CREATE TABLE contient_partition (
	partition_id INTEGER NOT NULL,
	album_id INTEGER NOT NULL,
	PRIMARY KEY (partition_id, album_id)
);

CREATE TABLE contient_user (
	user_id INTEGER NOT NULL,
	album_id INTEGER NOT NULL,
	PRIMARY KEY (user_id, album_id)
);
