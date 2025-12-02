CREATE TABLE Users (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  username TEXT NOT NULL UNIQUE,
  password_hash TEXT NOT NULL,
  email TEXT UNIQUE,
  full_name TEXT,
  created_at TEXT DEFAULT (datetime('now')),
  updated_at TEXT DEFAULT (datetime('now')),
  is_active INTEGER NOT NULL DEFAULT 1
);
CREATE TABLE sqlite_sequence(name,seq);
CREATE INDEX idx_users_username ON Users(username);
CREATE INDEX idx_users_email ON Users(email);
CREATE TABLE Sessions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL,
  session_token TEXT NOT NULL UNIQUE,
  created_at TEXT DEFAULT (datetime('now')),
  expires_at TEXT,
  FOREIGN KEY (user_id) REFERENCES Users(id) ON DELETE CASCADE
);
CREATE INDEX idx_sessions_token ON Sessions(session_token);
CREATE INDEX idx_sessions_user_id ON Sessions(user_id);
CREATE TABLE Revisions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  entity_type TEXT,
  entity_id INTEGER,
  author TEXT,
  change_json TEXT,
  created_at TEXT DEFAULT (datetime('now'))
);
CREATE TABLE People (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  given_name TEXT NOT NULL,
  family_name TEXT NOT NULL,
  other_names TEXT,
  gender TEXT,
  birth_date TEXT,
  death_date TEXT,
  birth_place TEXT,
  bio TEXT,
  privacy TEXT,
  relation TEXT,                    -- <--- added
  created_at TEXT DEFAULT (datetime('now')),
  updated_at TEXT DEFAULT (datetime('now')),
  is_deleted INTEGER NOT NULL DEFAULT 0,
  user_id INTEGER NOT NULL,
  FOREIGN KEY (user_id) REFERENCES Users(id) ON DELETE CASCADE
);
CREATE INDEX idx_people_user_id ON People(user_id);
CREATE INDEX idx_people_is_deleted ON People(is_deleted);
CREATE TABLE Relationships (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  person1_id INTEGER NOT NULL,
  person2_id INTEGER NOT NULL,
  type TEXT,
  details TEXT,
  start_date TEXT,
  end_date TEXT,
  created_at TEXT DEFAULT (datetime('now')),
  updated_at TEXT DEFAULT (datetime('now')),
  FOREIGN KEY (person1_id) REFERENCES People(id) ON DELETE CASCADE,
  FOREIGN KEY (person2_id) REFERENCES People(id) ON DELETE CASCADE
);
CREATE INDEX idx_relationships_person1 ON Relationships(person1_id);
CREATE INDEX idx_relationships_person2 ON Relationships(person2_id);
CREATE TABLE Media (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  filename TEXT,
  url TEXT,
  mime_type TEXT,
  caption TEXT,
  uploaded_by INTEGER,
  uploaded_at TEXT DEFAULT (datetime('now')),
  metadata_json TEXT,
  FOREIGN KEY (uploaded_by) REFERENCES Users(id) ON DELETE SET NULL
);
CREATE INDEX idx_media_uploaded_by ON Media(uploaded_by);
CREATE TABLE MediaLinks (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  media_id INTEGER NOT NULL,
  entity_type TEXT,
  entity_id INTEGER,
  role TEXT,
  FOREIGN KEY (media_id) REFERENCES Media(id) ON DELETE CASCADE
);
CREATE INDEX idx_medialinks_media_id ON MediaLinks(media_id);
CREATE TABLE Events (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  title TEXT,
  event_date TEXT,
  place TEXT,
  description TEXT,
  created_by INTEGER,
  user_id INTEGER,
  created_at TEXT DEFAULT (datetime('now')),
  updated_at TEXT DEFAULT (datetime('now')),
  FOREIGN KEY (created_by) REFERENCES People(id) ON DELETE SET NULL,
  FOREIGN KEY (user_id) REFERENCES Users(id) ON DELETE CASCADE
);
CREATE INDEX idx_events_user_id ON Events(user_id);
CREATE INDEX idx_events_created_by ON Events(created_by);
CREATE TABLE Sources (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  title TEXT,
  url TEXT,
  citation_text TEXT,
  created_at TEXT DEFAULT (datetime('now')),
  user_id INTEGER,
  FOREIGN KEY (user_id) REFERENCES Users(id) ON DELETE CASCADE
);
CREATE INDEX idx_sources_user_id ON Sources(user_id);
CREATE TABLE SourceLinks (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  source_id INTEGER NOT NULL,
  entity_type TEXT,
  entity_id INTEGER,
  note TEXT,
  FOREIGN KEY (source_id) REFERENCES Sources(id) ON DELETE CASCADE
);
CREATE INDEX idx_sourcelinks_source_id ON SourceLinks(source_id);
CREATE TABLE EventPeople (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  event_id INTEGER NOT NULL,
  person_id INTEGER NOT NULL,
  role TEXT,
  FOREIGN KEY (event_id) REFERENCES Events(id) ON DELETE CASCADE,
  FOREIGN KEY (person_id) REFERENCES People(id) ON DELETE CASCADE
);
CREATE INDEX idx_eventpeople_event_id ON EventPeople(event_id);
CREATE INDEX idx_eventpeople_person_id ON EventPeople(person_id);
