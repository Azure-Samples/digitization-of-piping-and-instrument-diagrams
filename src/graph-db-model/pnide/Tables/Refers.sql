/*
This edge table will store the edge information on connector to connector connectivites.
This edge will show that a connector is downstream of another connector.
*/
CREATE TABLE [pnide].[Refers] (
    CONSTRAINT EC_CONNECTION_REFERS CONNECTION ([pnide].[Connector] TO [pnide].[Connector]) ON DELETE CASCADE
) as EDGE;