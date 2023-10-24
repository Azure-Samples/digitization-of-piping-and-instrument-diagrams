/**
 This edge will be used to connect the assets to the sheet. This will show that the asset is a part of which sheet.
 */
CREATE TABLE [pnide].[IsPartOf] (
    CONSTRAINT EC_CONNECTION_IS_PART_OF CONNECTION ([pnide].[Asset] TO [pnide].[Sheet]) ON DELETE CASCADE
) as EDGE;