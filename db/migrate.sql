/* =========================================
   STEP 0: Begin Transaction
   ========================================= */
BEGIN TRANSACTION;

/* =========================================
   STEP 1: Drop all foreign keys
   ========================================= */
ALTER TABLE Relationships DROP CONSTRAINT FK_Relationships_person1_id;
ALTER TABLE Relationships DROP CONSTRAINT FK_Relationships_person2_id;

ALTER TABLE Media DROP CONSTRAINT FK_Media_uploaded_by;

ALTER TABLE MediaLinks DROP CONSTRAINT FK_MediaLinks_media_id;

ALTER TABLE Events DROP CONSTRAINT FK_Events_created_by;

ALTER TABLE SourceLinks DROP CONSTRAINT FK_SourceLinks_source_id;

ALTER TABLE EventPeople DROP CONSTRAINT FK_EventPeople_event_id;
ALTER TABLE EventPeople DROP CONSTRAINT FK_EventPeople_person_id;

/* =========================================
   STEP 2: Recreate tables with IDENTITY PKs
   ========================================= */

/* ---------- People ---------- */
CREATE TABLE People_new (
  id INT IDENTITY(1,1) PRIMARY KEY,
  given_name NVARCHAR(100),
  family_name NVARCHAR(100),
  other_names NVARCHAR(200),
  gender NVARCHAR(20),
  birth_date DATE,
  death_date DATE,
  birth_place NVARCHAR(255),
  bio NVARCHAR(MAX),
  privacy NVARCHAR(10),
  created_at DATETIME2,
  updated_at DATETIME2,
  is_deleted BIT
);

SET IDENTITY_INSERT People_new ON;
INSERT INTO People_new (id, given_name, family_name, other_names, gender,
                        birth_date, death_date, birth_place, bio, privacy,
                        created_at, updated_at, is_deleted)
SELECT id, given_name, family_name, other_names, gender,
       birth_date, death_date, birth_place, bio, privacy,
       created_at, updated_at, is_deleted
FROM People;
SET IDENTITY_INSERT People_new OFF;

DROP TABLE People;
EXEC sp_rename 'People_new', 'People';

/* ---------- Revisions ---------- */
CREATE TABLE Revisions_new (
  id INT IDENTITY(1,1) PRIMARY KEY,
  entity_type NVARCHAR(50),
  entity_id INT,
  author NVARCHAR(255),
  change_json NVARCHAR(MAX),
  created_at DATETIME2
);

SET IDENTITY_INSERT Revisions_new ON;
INSERT INTO Revisions_new (id, entity_type, entity_id, author, change_json, created_at)
SELECT id, entity_type, entity_id, author, change_json, created_at FROM Revisions;
SET IDENTITY_INSERT Revisions_new OFF;

DROP TABLE Revisions;
EXEC sp_rename 'Revisions_new', 'Revisions';

/* ---------- Relationships ---------- */
CREATE TABLE Relationships_new (
  id INT IDENTITY(1,1) PRIMARY KEY,
  person1_id INT,
  person2_id INT,
  type NVARCHAR(20),
  details NVARCHAR(255),
  start_date DATE,
  end_date DATE,
  created_at DATETIME2,
  updated_at DATETIME2
);

SET IDENTITY_INSERT Relationships_new ON;
INSERT INTO Relationships_new (id, person1_id, person2_id, type, details,
                               start_date, end_date, created_at, updated_at)
SELECT id, person1_id, person2_id, type, details,
       start_date, end_date, created_at, updated_at
FROM Relationships;
SET IDENTITY_INSERT Relationships_new OFF;

DROP TABLE Relationships;
EXEC sp_rename 'Relationships_new', 'Relationships';

/* ---------- Media ---------- */
CREATE TABLE Media_new (
  id INT IDENTITY(1,1) PRIMARY KEY,
  filename NVARCHAR(255),
  url NVARCHAR(500),
  mime_type NVARCHAR(100),
  caption NVARCHAR(255),
  uploaded_by INT,
  uploaded_at DATETIME2,
  metadata_json NVARCHAR(MAX)
);

SET IDENTITY_INSERT Media_new ON;
INSERT INTO Media_new (id, filename, url, mime_type, caption, uploaded_by, uploaded_at, metadata_json)
SELECT id, filename, url, mime_type, caption, uploaded_by, uploaded_at, metadata_json
FROM Media;
SET IDENTITY_INSERT Media_new OFF;

DROP TABLE Media;
EXEC sp_rename 'Media_new', 'Media';

/* ---------- MediaLinks ---------- */
CREATE TABLE MediaLinks_new (
  id INT IDENTITY(1,1) PRIMARY KEY,
  media_id INT,
  entity_type NVARCHAR(50),
  entity_id INT,
  role NVARCHAR(50)
);

SET IDENTITY_INSERT MediaLinks_new ON;
INSERT INTO MediaLinks_new (id, media_id, entity_type, entity_id, role)
SELECT id, media_id, entity_type, entity_id, role
FROM MediaLinks;
SET IDENTITY_INSERT MediaLinks_new OFF;

DROP TABLE MediaLinks;
EXEC sp_rename 'MediaLinks_new', 'MediaLinks';

/* ---------- Events ---------- */
CREATE TABLE Events_new (
  id INT IDENTITY(1,1) PRIMARY KEY,
  title NVARCHAR(255),
  event_date DATE,
  place NVARCHAR(255),
  description NVARCHAR(MAX),
  created_by INT,
  created_at DATETIME2,
  updated_at DATETIME2
);

SET IDENTITY_INSERT Events_new ON;
INSERT INTO Events_new (id, title, event_date, place, description, created_by, created_at, updated_at)
SELECT id, title, event_date, place, description, created_by, created_at, updated_at
FROM Events;
SET IDENTITY_INSERT Events_new OFF;

DROP TABLE Events;
EXEC sp_rename 'Events_new', 'Events';

/* ---------- Sources ---------- */
CREATE TABLE Sources_new (
  id INT IDENTITY(1,1) PRIMARY KEY,
  title NVARCHAR(255),
  url NVARCHAR(500),
  citation_text NVARCHAR(MAX),
  created_at DATETIME2
);

SET IDENTITY_INSERT Sources_new ON;
INSERT INTO Sources_new (id, title, url, citation_text, created_at)
SELECT id, title, url, citation_text, created_at
FROM Sources;
SET IDENTITY_INSERT Sources_new OFF;

DROP TABLE Sources;
EXEC sp_rename 'Sources_new', 'Sources';

/* ---------- SourceLinks ---------- */
CREATE TABLE SourceLinks_new (
  id INT IDENTITY(1,1) PRIMARY KEY,
  source_id INT,
  entity_type NVARCHAR(50),
  entity_id INT,
  note NVARCHAR(255)
);

SET IDENTITY_INSERT SourceLinks_new ON;
INSERT INTO SourceLinks_new (id, source_id, entity_type, entity_id, note)
SELECT id, source_id, entity_type, entity_id, note
FROM SourceLinks;
SET IDENTITY_INSERT SourceLinks_new OFF;

DROP TABLE SourceLinks;
EXEC sp_rename 'SourceLinks_new', 'SourceLinks';

/* ---------- EventPeople ---------- */
CREATE TABLE EventPeople_new (
  id INT IDENTITY(1,1) PRIMARY KEY,
  event_id INT,
  person_id INT,
  role NVARCHAR(50)
);

SET IDENTITY_INSERT EventPeople_new ON;
INSERT INTO EventPeople_new (id, event_id, person_id, role)
SELECT id, event_id, person_id, role
FROM EventPeople;
SET IDENTITY_INSERT EventPeople_new OFF;

DROP TABLE EventPeople;
EXEC sp_rename 'EventPeople_new', 'EventPeople';

/* =========================================
   STEP 3: Recreate foreign keys
   ========================================= */
ALTER TABLE Relationships
  ADD CONSTRAINT FK_Relationships_person1_id FOREIGN KEY (person1_id)
  REFERENCES People(id);

ALTER TABLE Relationships
  ADD CONSTRAINT FK_Relationships_person2_id FOREIGN KEY (person2_id)
  REFERENCES People(id);

ALTER TABLE Media
  ADD CONSTRAINT FK_Media_uploaded_by FOREIGN KEY (uploaded_by)
  REFERENCES People(id);

ALTER TABLE MediaLinks
  ADD CONSTRAINT FK_MediaLinks_media_id FOREIGN KEY (media_id)
  REFERENCES Media(id);

ALTER TABLE Events
  ADD CONSTRAINT FK_Events_created_by FOREIGN KEY (created_by)
  REFERENCES People(id);

ALTER TABLE SourceLinks
  ADD CONSTRAINT FK_SourceLinks_source_id FOREIGN KEY (source_id)
  REFERENCES Sources(id);

ALTER TABLE EventPeople
  ADD CONSTRAINT FK_EventPeople_event_id FOREIGN KEY (event_id)
  REFERENCES Events(id);

ALTER TABLE EventPeople
  ADD CONSTRAINT FK_EventPeople_person_id FOREIGN KEY (person_id)
  REFERENCES People(id);

/* =========================================
   STEP 4: Commit Transaction
   ========================================= */
COMMIT TRANSACTION;

PRINT 'Migration completed successfully. All tables now have IDENTITY primary keys.';

