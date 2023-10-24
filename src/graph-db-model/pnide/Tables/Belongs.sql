/*
This edge table will store the edge information between sheets and PNIDs. This edge will show that a sheet belongs to a PNID.
*/
CREATE TABLE [pnid].[Belongs] (
    CONSTRAINT EC_CONNECTION_BELONGS CONNECTION ([pnide].[Sheet] TO [pnide].[PNID]) ON DELETE CASCADE
) as EDGE;