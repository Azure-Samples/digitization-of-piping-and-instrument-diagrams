/*
The connector node will store the connector information including the text associated and attributes. The attributes will be stored as a JSON string.

The id will be the sheet id + the connector id.

For example:
| Id          | text_associated          | Attributes                                                                               |
|-------------|--------------------------|------------------------------------------------------------------------------------------|
| 123-D0001-1 | 1101:01 RAW FEED TO 1703 | `{ "bounding_box": { "topX": 0.0, "topY": 0.0,  "bottomX": 0.2, "bottomY": 0.2 }, ... }` |
*/
CREATE TABLE [pnide].[Connector]
(
    [Id] NVARCHAR(255) NOT NULL PRIMARY KEY,
    [text_associated] NVARCHAR(255) NULL,
    [attributes] NVARCHAR(MAX) NULL,
) as NODE;
