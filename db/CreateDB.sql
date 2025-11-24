/* =========================================
   CONFIG: Set these three values
   ========================================= */
DECLARE @DbName        sysname        = N'demoDB';
DECLARE @LoginName     sysname        = N'test';
DECLARE @LoginPassword nvarchar(128)  = N'test@123';


/* =========================================
   1. Create Database if NOT EXISTS
   ========================================= */
IF DB_ID(@DbName) IS NULL
BEGIN
    DECLARE @sqlCreateDb nvarchar(max) =
        N'CREATE DATABASE ' + QUOTENAME(@DbName) + N';';

    PRINT 'Creating database ' + @DbName;
    EXEC (@sqlCreateDb);
END
ELSE
BEGIN
    PRINT 'Database ' + @DbName + ' already exists.';
END;


/* =========================================
   2. Create LOGIN (server-level) if NOT EXISTS
   ========================================= */
IF NOT EXISTS (
    SELECT 1
    FROM sys.server_principals
    WHERE name = @LoginName
)
BEGIN
    DECLARE @sqlCreateLogin nvarchar(max) =
        N'CREATE LOGIN ' + QUOTENAME(@LoginName) +
        N' WITH PASSWORD = ' + QUOTENAME(@LoginPassword, '''') + N',
           CHECK_POLICY = OFF;';

    PRINT 'Creating login ' + @LoginName;
    EXEC (@sqlCreateLogin);
END
ELSE
BEGIN
    PRINT 'Login ' + @LoginName + ' already exists.';
END;


/* =========================================
   3. Create USER in the database & Grant Permissions
      - db_datareader : SELECT all tables
      - db_datawriter : INSERT/UPDATE/DELETE all tables
   ========================================= */
DECLARE @sqlUserAndPerms nvarchar(max) = N'
USE ' + QUOTENAME(@DbName) + N';

-- Create user if missing
IF NOT EXISTS (
    SELECT 1
    FROM sys.database_principals
    WHERE name = ' + QUOTENAME(@LoginName, '''') + N'
)
BEGIN
    PRINT ''Creating user ' + @LoginName + ' in database ' + @DbName + ''';
    CREATE USER ' + QUOTENAME(@LoginName) + N'
        FOR LOGIN ' + QUOTENAME(@LoginName) + N';
END
ELSE
BEGIN
    PRINT ''User ' + @LoginName + ' already exists in database ' + @DbName + ''';
END;

-- Grant READ access (SELECT)
ALTER ROLE db_datareader ADD MEMBER ' + QUOTENAME(@LoginName) + N';

-- Grant WRITE access (INSERT/UPDATE/DELETE)
ALTER ROLE db_datawriter ADD MEMBER ' + QUOTENAME(@LoginName) + N';
';

PRINT 'Assigning permissions in database ' + @DbName;
EXEC (@sqlUserAndPerms);

