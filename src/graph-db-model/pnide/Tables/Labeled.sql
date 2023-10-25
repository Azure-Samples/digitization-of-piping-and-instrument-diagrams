CREATE TABLE [pnide].[Labeled] (
    CONSTRAINT EC_CONNECTION_LABELED CONNECTION ([pnide].[Asset] TO [pnide].[AssetType]) ON DELETE CASCADE
) as EDGE;