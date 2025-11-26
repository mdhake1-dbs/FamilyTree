/* ====== CONFIG: Set these values (change before running) ====== */
DECLARE @DbName        sysname       = N'demoDB1';
DECLARE @LoginName     sysname       = N'test1';
DECLARE @LoginPassword nvarchar(128) = N'test@1231';

/* ====== 1) Create database if not exists ====== */
IF DB_ID(@DbName) IS NULL
BEGIN
    DECLARE @sqlCreateDb nvarchar(max) = N'CREATE DATABASE ' + QUOTENAME(@DbName) + N';';
    PRINT 'Creating database ' + @DbName;
    EXEC (@sqlCreateDb);
END
ELSE
BEGIN
    PRINT 'Database ' + @DbName + ' already exists.';
END;

/* ====== 2) Create or ALTER LOGIN (server-level). ======
   If the login already exists we ALTER it to set the password.
   Note: ALTER LOGIN requires appropriate server-level permissions.
   CHECK_POLICY / CHECK_EXPIRATION set to OFF for dev; enable in production.
===== */
IF EXISTS (SELECT 1 FROM sys.server_principals WHERE name = @LoginName)
BEGIN
    PRINT 'Login ' + @LoginName + ' already exists - altering password (if permitted).';
    DECLARE @sqlAlterLogin nvarchar(max) =
        N'ALTER LOGIN ' + QUOTENAME(@LoginName) +
        N' WITH PASSWORD = ' + QUOTENAME(@LoginPassword, '''') + N', CHECK_POLICY = OFF, CHECK_EXPIRATION = OFF;';
    BEGIN TRY
        EXEC (@sqlAlterLogin);
    END TRY
    BEGIN CATCH
        PRINT 'Warning: ALTER LOGIN failed or insufficient permission. You may need to change the login password manually.';
        PRINT ERROR_MESSAGE();
    END CATCH
END
ELSE
BEGIN
    DECLARE @sqlCreateLogin nvarchar(max) =
        N'CREATE LOGIN ' + QUOTENAME(@LoginName) +
        N' WITH PASSWORD = ' + QUOTENAME(@LoginPassword, '''') + N', CHECK_POLICY = OFF, CHECK_EXPIRATION = OFF;';
    PRINT 'Creating login ' + @LoginName;
    EXEC (@sqlCreateLogin);
END

/* ====== 3) Create database user and assign DB roles ======
   This block is executed in dynamic SQL so we can use QUOTENAME(@DbName) safely.
   We:
   - USE the target DB
   - CREATE USER FOR LOGIN if needed
   - Set DEFAULT_SCHEMA = dbo
   - Add to db_datareader & db_datawriter
===== */
DECLARE @sqlUserAndPerms nvarchar(max) = N'
USE ' + QUOTENAME(@DbName) + N';

-- Create user if missing
IF NOT EXISTS (
    SELECT 1 FROM sys.database_principals WHERE name = ' + QUOTENAME(@LoginName, '''') + N'
)
BEGIN
    PRINT ''Creating database user ' + @LoginName + ' in ' + @DbName + ''';
    CREATE USER ' + QUOTENAME(@LoginName) + N' FOR LOGIN ' + QUOTENAME(@LoginName) + N' WITH DEFAULT_SCHEMA = dbo;
END
ELSE
BEGIN
    PRINT ''User ' + @LoginName + ' already exists in database ' + @DbName + ''';
END

-- Add to reader/writer roles (no-op if already member)
IF NOT EXISTS (
    SELECT 1 FROM sys.database_role_members drm
    JOIN sys.database_principals r ON drm.role_principal_id = r.principal_id
    JOIN sys.database_principals m ON drm.member_principal_id = m.principal_id
    WHERE r.name = ''db_datareader'' AND m.name = ' + QUOTENAME(@LoginName, '''') + N'
)
BEGIN
    ALTER ROLE db_datareader ADD MEMBER ' + QUOTENAME(@LoginName) + N';
END

IF NOT EXISTS (
    SELECT 1 FROM sys.database_role_members drm
    JOIN sys.database_principals r ON drm.role_principal_id = r.principal_id
    JOIN sys.database_principals m ON drm.member_principal_id = m.principal_id
    WHERE r.name = ''db_datawriter'' AND m.name = ' + QUOTENAME(@LoginName, '''') + N'
)
BEGIN
    ALTER ROLE db_datawriter ADD MEMBER ' + QUOTENAME(@LoginName) + N';
END
';

PRINT 'Assigning permissions in database ' + @DbName;
EXEC (@sqlUserAndPerms);

PRINT 'Script completed. Verify connectivity and permissions as required.';

