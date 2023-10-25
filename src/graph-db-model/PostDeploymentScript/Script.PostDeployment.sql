/*
Post-Deployment Script Template							
--------------------------------------------------------------------------------------
 This file contains SQL statements that will be appended to the build script.		
 Use SQLCMD syntax to include a file in the post-deployment script.			
 Example:      :r .\myfile.sql								
 Use SQLCMD syntax to reference a variable in the post-deployment script.		
 Example:      :setvar TableName MyTable							
               SELECT * FROM [$(TableName)]					
--------------------------------------------------------------------------------------


-- More Post deploy files can be included in this file

:r ./EngineSeedData.sql
:r ./SystemCatalogsData.sql
:r ./ReasonCodeReferenceSeedData.sql
:r ./ReportingPeriodConfigurationSeedData.sql
:r ./ReasonCodeSeedData.sql



:r ./Analytics_SeedData.sql
:r ./WorkerCategorySeedData.sql
:r ./WorkOrderDepartment_SeedData.sql
*/