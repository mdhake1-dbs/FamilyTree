PRAGMA foreign_keys = ON;

-- Add Users table for authentication
CREATE TABLE Users (
  id INTEGER PRIMARY KEY,
  username TEXT UNIQUE NOT NULL,
  password_hash TEXT NOT NULL,
  email TEXT UNIQUE,
  full_name TEXT,
  created_at TEXT,
  updated_at TEXT,
  is_active INTEGER DEFAULT 1
);

CREATE INDEX idx_users_username ON Users(username);
CREATE INDEX idx_users_email ON Users(email);

CREATE TABLE Sessions (
  id INTEGER PRIMARY KEY,
  user_id INTEGER NOT NULL,
  session_token TEXT UNIQUE NOT NULL,
  created_at TEXT,
  expires_at TEXT,
  FOREIGN KEY (user_id) REFERENCES Users(id)
);

CREATE INDEX idx_sessions_token ON Sessions(session_token);
CREATE INDEX idx_sessions_user_id ON Sessions(user_id);

-- ===========================
-- Revisions
-- ===========================
CREATE TABLE Revisions (
  id INTEGER PRIMARY KEY,
  entity_type TEXT,
  entity_id INTEGER,
  author TEXT,
  change_json TEXT,
  created_at TEXT
);

-- ===========================
-- People
-- ===========================
CREATE TABLE People (
  id INTEGER PRIMARY KEY,
  given_name TEXT,
  family_name TEXT,
  other_names TEXT,
  gender TEXT,
  birth_date TEXT,
  death_date TEXT,
  birth_place TEXT,
  bio TEXT,
  privacy TEXT,
  created_at TEXT,
  updated_at TEXT,
  is_deleted INTEGER,
  user_id INTEGER REFERENCES Users(id)
);

CREATE INDEX idx_people_id ON People(id);

-- ===========================
-- Relationships
-- ===========================
CREATE TABLE Relationships (
  id INTEGER PRIMARY KEY,
  person1_id INTEGER,
  person2_id INTEGER,
  type TEXT,
  details TEXT,
  start_date TEXT,
  end_date TEXT,
  created_at TEXT,
  updated_at TEXT,
  FOREIGN KEY (person1_id) REFERENCES People(id),
  FOREIGN KEY (person2_id) REFERENCES People(id)
);

-- ===========================
-- Media
-- ===========================
CREATE TABLE Media (
  id INTEGER PRIMARY KEY,
  filename TEXT,
  url TEXT,
  mime_type TEXT,
  caption TEXT,
  uploaded_by INTEGER,
  uploaded_at TEXT,
  metadata_json TEXT,
  FOREIGN KEY (uploaded_by) REFERENCES People(id)
);

-- ===========================
-- MediaLinks
-- ===========================
CREATE TABLE MediaLinks (
  id INTEGER PRIMARY KEY,
  media_id INTEGER,
  entity_type TEXT,
  entity_id INTEGER,
  role TEXT,
  FOREIGN KEY (media_id) REFERENCES Media(id)
);

-- ===========================
-- Events
-- ===========================
CREATE TABLE Events (
  id INTEGER PRIMARY KEY,
  title TEXT,
  event_date TEXT,
  place TEXT,
  description TEXT,
  created_by INTEGER REFERENCES People(id),
  user_id INTEGER REFERENCES Users(id),
  created_at TEXT,
  updated_at TEXT
);

-- ===========================
-- Sources
-- ===========================
CREATE TABLE Sources (
  id INTEGER PRIMARY KEY,
  title TEXT,
  url TEXT,
  citation_text TEXT,
  created_at TEXT,
  user_id INTEGER REFERENCES Users(id)
);

-- ===========================
-- SourceLinks
-- ===========================
CREATE TABLE SourceLinks (
  id INTEGER PRIMARY KEY,
  source_id INTEGER,
  entity_type TEXT,
  entity_id INTEGER,
  note TEXT,
  FOREIGN KEY (source_id) REFERENCES Sources(id)
);

-- ===========================
-- EventPeople
-- ===========================
CREATE TABLE EventPeople (
  id INTEGER PRIMARY KEY,
  event_id INTEGER,
  person_id INTEGER,
  role TEXT,
  FOREIGN KEY (event_id) REFERENCES Events(id),
  FOREIGN KEY (person_id) REFERENCES People(id)
);

