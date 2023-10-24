/**

The sheet node will be used to store the diagram information located in a sheet of an PnID diagram. The sheet node will also store 
any metadata associated with the sheet as a json string into attributes including the size of image and the inclusive box specifying
the area of the main diagram.

Where `Id` is the unique identifier for the sheet, `name` is the name of the sheet, and `attributes` is the attributes of the sheet in json format
including the size of image and the inclusive box specifying the area of the main diagram. `Id` will be a combination of the PNID Id and sheet number.

Example:

| Id       | Name                                       | Attributes                                                   |
|----------|--------------------------------------------|--------------------------------------------------------------|
| 123-D001 | Sheet 1: Truck Unloading and Transfer Pack | `{ "image_details": { "width": 1024, "height": 768 }, ... }` |
| 123-D100 | Sheet 2: Air Stripper and Deformer         | `{ "image_details": { "width": 1024, "height": 768 }, ... }` |

 */
CREATE TABLE [pnide].[Sheet]
(
    [Id] NVARCHAR(255) NOT NULL PRIMARY KEY,
    [name] NVARCHAR(255) NOT NULL,
    [attributes] NVARCHAR(MAX) NULL,
) as NODE;

