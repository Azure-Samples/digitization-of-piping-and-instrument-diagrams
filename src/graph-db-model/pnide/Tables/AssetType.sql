/*
This node will store the asset type information including id, category, sub-category, display name and unique string.

For example:

| Id  | category   | subcategory | displayname       | uniquestring                       |
|-----|------------|-------------|-------------------|------------------------------------|
| 1	  | Instrument | Valve       | Welded gate valve | Instrument/Valve/Welded gate valve |
*/
CREATE TABLE [pnid].[AssetType]
(
    [Id] int NOT NULL IDENTITY(1,1) PRIMARY KEY,
    [category] NVARCHAR(255) NOT NULL,
    [subcategory] NVARCHAR(255) NOT NULL,
    [displayname] NVARCHAR(255) NOT NULL,
    [uniquestring] AS ([category] + '/' + [subcategory] + '/' + [displayname]) PERSISTED UNIQUE
) as NODE;