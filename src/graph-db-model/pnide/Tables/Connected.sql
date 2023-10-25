/*
This edge table will store the edge information on asset connectivites.
This edge will show that an asset is either downstream or upstream of another asset.
flow_direction: 0 = unknown, 1 = upstream, 2 = downstream
segment: JSON string of the lines and symbols that connect the two assets. This will be a list of all segments.
*/
CREATE TABLE [pnide].[Connected] (
    [segments] NVARCHAR(MAX) NULL,
    CONSTRAINT EC_CONNECTION_CONNECTED CONNECTION ([pnide].[Asset] TO [pnide].[Asset]) ON DELETE CASCADE
) as EDGE;