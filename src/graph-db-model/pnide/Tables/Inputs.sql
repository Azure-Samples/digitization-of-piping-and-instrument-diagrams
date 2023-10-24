/**
 This edge will will show the input from an asset to a connector in the sheet.
 */
CREATE TABLE [pnide].[Inputs] (
    CONSTRAINT EC_CONNECTION_INPUTS CONNECTION ([pnide].[Asset] TO [pnide].[Connector]) ON DELETE CASCADE
) as EDGE;