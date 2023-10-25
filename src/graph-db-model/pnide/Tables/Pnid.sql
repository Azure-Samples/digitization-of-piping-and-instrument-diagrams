/**
This node will store the PnID diagram information including any metadata associated with the diagram as a json string into attributes.
Where `Id` is the unique identifier for the PnID diagram, `name` is the name of the PnID, and `attributes` is the attributes
of the PnID in json format.

| Id  | Name                                           | Attributes                                                              |
|-----|------------------------------------------------|-------------------------------------------------------------------------|
| 123 | Pipping and Instrumentation - Central Training | `{ "issue_date": "August 2019", "issue_for": "Central Training", ... }` |
 */
CREATE TABLE [pnide].[PNID]
(
    [Id] NVARCHAR(255) NOT NULL PRIMARY KEY,
    [name] NVARCHAR(255) NOT NULL,
    [attributes] NVARCHAR(MAX) NULL,
) as NODE;

