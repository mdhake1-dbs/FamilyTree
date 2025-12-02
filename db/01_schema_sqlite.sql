PRAGMA foreign_keys = ON;

-- Users table
CREATE TABLE IF NOT EXISTS Users (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  username TEXT NOT NULL UNIQUE,
  password_hash TEXT NOT NULL,
  email TEXT UNIQUE,
  full_name TEXT,
  created_at TEXT DEFAULT (datetime('now')),
  updated_at TEXT DEFAULT (datetime('now')),
  is_active INTEGER NOT NULL DEFAULT 1
);

-- Indexes on Users
CREATE INDEX IF NOT EXISTS idx_users_username ON Users(username);
CREATE INDEX IF NOT EXISTS idx_users_email    ON Users(email);

-- Sessions table
CREATE TABLE IF NOT EXISTS Sessions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL,
  session_token TEXT NOT NULL UNIQUE,
  created_at TEXT DEFAULT (datetime('now')),
  expires_at TEXT,
  FOREIGN KEY (user_id) REFERENCES Users(id) ON DELETE CASCADE
);

-- Indexes on Sessions
CREATE INDEX IF NOT EXISTS idx_sessions_token   ON Sessions(session_token);
CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON Sessions(user_id);

-- People table
CREATE TABLE IF NOT EXISTS People (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  given_name  TEXT NOT NULL,
  family_name TEXT NOT NULL,
  other_names TEXT,
  gender      TEXT,
  birth_date  TEXT,
  death_date  TEXT,
  birth_place TEXT,
  bio         TEXT,
  privacy     TEXT,
  relation    TEXT,                    -- existing field kept
  created_at  TEXT DEFAULT (datetime('now')),
  updated_at  TEXT DEFAULT (datetime('now')),
  is_deleted  INTEGER NOT NULL DEFAULT 0,
  user_id     INTEGER NOT NULL,
  FOREIGN KEY (user_id) REFERENCES Users(id) ON DELETE CASCADE
);

-- Indexes on People
CREATE INDEX IF NOT EXISTS idx_people_user_id    ON People(user_id);
CREATE INDEX IF NOT EXISTS idx_people_is_deleted ON People(is_deleted);

-- Relationships table
CREATE TABLE IF NOT EXISTS Relationships (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  person1_id INTEGER NOT NULL,
  person2_id INTEGER NOT NULL,
  type       TEXT,
  details    TEXT,
  start_date TEXT,
  end_date   TEXT,
  created_at TEXT DEFAULT (datetime('now')),
  updated_at TEXT DEFAULT (datetime('now')),
  FOREIGN KEY (person1_id) REFERENCES People(id) ON DELETE CASCADE,
  FOREIGN KEY (person2_id) REFERENCES People(id) ON DELETE CASCADE
);

-- Indexes on Relationships
CREATE INDEX IF NOT EXISTS idx_relationships_person1 ON Relationships(person1_id);
CREATE INDEX IF NOT EXISTS idx_relationships_person2 ON Relationships(person2_id);

-- Events table
CREATE TABLE IF NOT EXISTS Events (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  title       TEXT,
  event_date  TEXT,
  place       TEXT,
  description TEXT,
  created_by  INTEGER,
  user_id     INTEGER,
  created_at  TEXT DEFAULT (datetime('now')),
  updated_at  TEXT DEFAULT (datetime('now')),
  FOREIGN KEY (created_by) REFERENCES People(id) ON DELETE SET NULL,
  FOREIGN KEY (user_id)    REFERENCES Users(id)  ON DELETE CASCADE
);

-- Indexes on Events
CREATE INDEX IF NOT EXISTS idx_events_user_id    ON Events(user_id);
CREATE INDEX IF NOT EXISTS idx_events_created_by ON Events(created_by);

-- EventPeople table
CREATE TABLE IF NOT EXISTS EventPeople (
  id        INTEGER PRIMARY KEY AUTOINCREMENT,
  event_id  INTEGER NOT NULL,
  person_id INTEGER NOT NULL,
  role      TEXT,
  FOREIGN KEY (event_id)  REFERENCES Events(id)  ON DELETE CASCADE,
  FOREIGN KEY (person_id) REFERENCES People(id) ON DELETE CASCADE
);

-- Indexes on EventPeople
CREATE INDEX IF NOT EXISTS idx_eventpeople_event_id  ON EventPeople(event_id);
CREATE INDEX IF NOT EXISTS idx_eventpeople_person_id ON EventPeople(person_id);

