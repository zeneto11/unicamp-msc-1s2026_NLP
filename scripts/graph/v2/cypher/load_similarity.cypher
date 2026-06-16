LOAD CSV WITH HEADERS FROM 'file:///aletheia_pt_v2/message_similarity.csv' AS row
MATCH (s:Message {id: row.source_message_id})
MATCH (t:Message {id: row.target_message_id})
MERGE (s)-[r:SIMILAR_TO]->(t)
SET
  r.cosine_similarity = toFloat(row.cosine_similarity),
  r.rank = toInteger(row.rank),
  r.method = row.method,
  r.embedding_model = row.embedding_model;
