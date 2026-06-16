LOAD CSV WITH HEADERS FROM 'file:///aletheia_pt_v2/communities.csv' AS row
MERGE (c:Community {id: toInteger(row.id)})
SET
  c.size = toInteger(row.size),
  c.density = toFloat(row.density),
  c.modularity = toFloat(row.modularity),
  c.algorithm = row.algorithm,
  c.community_name = row.community_name,
  c.descriptive_keywords = CASE
    WHEN row.descriptive_keywords = '' THEN []
    ELSE split(row.descriptive_keywords, '|')
  END,
  c.keyword_method = row.keyword_method;

LOAD CSV WITH HEADERS FROM 'file:///aletheia_pt_v2/channel_community.csv' AS row
MATCH (ch:Channel {id: row.channel_id})
MATCH (co:Community {id: toInteger(row.community_id)})
MERGE (ch)-[:BELONGS_TO]->(co);
