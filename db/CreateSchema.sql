CREATE TABLE [Revisions] (
  [id] int,
  [entity_type] nvarchar(50),
  [entity_id] int,
  [author] nvarchar(255),
  [change_json] nvarchar,
  [created_at] datetime2,
  PRIMARY KEY ([id])
);

CREATE TABLE [People] (
  [id] int,
  [given_name] nvarchar(100),
  [family_name] nvarchar(100),
  [other_names] nvarchar(200),
  [gender] nvarchar(20),
  [birth_date] date,
  [death_date] date,
  [birth_place] nvarchar(255),
  [bio] nvarchar,
  [privacy] nvarchar(10),
  [created_at] datetime2,
  [updated_at] datetime2,
  [is_deleted] bit,
  PRIMARY KEY ([id])
);

CREATE TABLE [Relationships] (
  [id] int,
  [person1_id] int,
  [person2_id] int,
  [type] nvarchar(20),
  [details] nvarchar(255),
  [start_date] date,
  [end_date] date,
  [created_at] datetime2,
  [updated_at] datetime2,
  PRIMARY KEY ([id]),
  CONSTRAINT [FK_Relationships_person2_id]
    FOREIGN KEY ([person2_id])
      REFERENCES [People]([id]),
  CONSTRAINT [FK_Relationships_person1_id]
    FOREIGN KEY ([person1_id])
      REFERENCES [People]([id])
);

CREATE TABLE [Media] (
  [id] int,
  [filename] nvarchar(255),
  [url] nvarchar(500),
  [mime_type] nvarchar(100),
  [caption] nvarchar(255),
  [uploaded_by] int,
  [uploaded_at] datetime2,
  [metadata_json] nvarchar,
  PRIMARY KEY ([id]),
  CONSTRAINT [FK_Media_uploaded_by]
    FOREIGN KEY ([uploaded_by])
      REFERENCES [People]([id])
);

CREATE TABLE [MediaLinks] (
  [id] int,
  [media_id] int,
  [entity_type] nvarchar(50),
  [entity_id] int,
  [role] nvarchar(50),
  PRIMARY KEY ([id]),
  CONSTRAINT [FK_MediaLinks_media_id]
    FOREIGN KEY ([media_id])
      REFERENCES [Media]([id])
);

CREATE TABLE [Events] (
  [id] int,
  [title] nvarchar(255),
  [event_date] date,
  [place] nvarchar(255),
  [description] nvarchar,
  [created_by] int,
  [created_at] datetime2,
  [updated_at] datetime2,
  PRIMARY KEY ([id]),
  CONSTRAINT [FK_Events_created_by]
    FOREIGN KEY ([created_by])
      REFERENCES [People]([id])
);

CREATE TABLE [Sources] (
  [id] int,
  [title] nvarchar(255),
  [url] nvarchar(500),
  [citation_text] nvarchar,
  [created_at] datetime2,
  PRIMARY KEY ([id])
);

CREATE TABLE [SourceLinks] (
  [id] int,
  [source_id] int,
  [entity_type] nvarchar(50),
  [entity_id] int,
  [note] nvarchar(255),
  PRIMARY KEY ([id]),
  CONSTRAINT [FK_SourceLinks_source_id]
    FOREIGN KEY ([source_id])
      REFERENCES [Sources]([id])
);

CREATE TABLE [EventPeople] (
  [id] int,
  [event_id] int,
  [person_id] int,
  [role] nvarchar(50),
  PRIMARY KEY ([id]),
  CONSTRAINT [FK_EventPeople_event_id]
    FOREIGN KEY ([event_id])
      REFERENCES [Events]([id]),
  CONSTRAINT [FK_EventPeople_person_id]
    FOREIGN KEY ([person_id])
      REFERENCES [People]([id])
);


