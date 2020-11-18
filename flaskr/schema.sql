DROP TABLE IF EXISTS user;
DROP TABLE IF EXISTS project;

CREATE TABLE user (
  idUser INTEGER PRIMARY KEY AUTOINCREMENT,
  fullName TEXT NOT NULL,
  email TEXT UNIQUE NOT NULL,
  enterprise TEXT NOT NULL,
  password TEXT NOT NULL
);

CREATE TABLE project (
  idProject INTEGER PRIMARY KEY AUTOINCREMENT,
  idUser INTEGER NOT NULL,
  name TEXT NOT NULL,
  use TEXT,
  file TEXT,
  FOREIGN KEY(idUser) REFERENCES user(idUser)
);
