/**
 This edge will show the output from a connector to an asset in the same/different sheet.
 */
CREATE TABLE [pnide].[Outputs] (
    CONSTRAINT EC_CONNECTION_OUTPUTS CONNECTION ([pnide].[Connector] TO [pnide].[Asset]) ON DELETE CASCADE
) as EDGE;