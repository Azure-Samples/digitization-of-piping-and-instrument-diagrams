/**
  This edge will be used to show the connectors is resided in which sheet.
 */
CREATE TABLE [pnide].[Resides] (
    CONSTRAINT EC_CONNECTION_RESIDES CONNECTION ([pnide].[Connector] TO [pnide].[Sheet]) ON DELETE CASCADE
) as EDGE;