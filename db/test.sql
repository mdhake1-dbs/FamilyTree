USE demoDB;

SELECT 
    dp.name AS UserName,
    dr.name AS RoleName
FROM sys.database_role_members rm
JOIN sys.database_principals dp ON rm.member_principal_id = dp.principal_id
JOIN sys.database_principals dr ON rm.role_principal_id   = dr.principal_id
WHERE dp.name = 'test';

