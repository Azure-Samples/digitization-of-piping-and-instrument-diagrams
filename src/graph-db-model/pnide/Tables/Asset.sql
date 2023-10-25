/*
This node will store the asset information including the text associated and attributes. The attributes will be stored as a JSON string.

For example:

| Id         | Text_associated | Attributes                                                                               |
|------------|-----------------|------------------------------------------------------------------------------------------|
| 123-D001-1 | 2" V1411        | `{ "bounding_box": { "topX": 0.0, "topY": 0.0,  "bottomX": 0.2, "bottomY": 0.2 }, ... }` |
*/
CREATE TABLE [pnide].[Asset]
(
  [Id] NVARCHAR(255) NOT NULL PRIMARY KEY,
  [text_associated] NVARCHAR(255) NULL,
  [attributes] NVARCHAR(MAX) NULL,
) as NODE;
