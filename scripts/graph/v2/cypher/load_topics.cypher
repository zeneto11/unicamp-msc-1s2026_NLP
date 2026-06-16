LOAD CSV WITH HEADERS FROM 'file:///aletheia_pt_v2/topics.csv' AS row
WITH row WHERE toInteger(row.id) <> -1
MERGE (t:Topic {id: toInteger(row.id)})
SET
  t.label = row.label,
  t.keywords = CASE
    WHEN row.keywords = '' THEN []
    ELSE split(row.keywords, '|')
  END,
  t.coherence_score = CASE
    WHEN row.coherence_score = '' THEN null
    ELSE toFloat(row.coherence_score)
  END,
  t.message_count = toInteger(row.message_count),
  t.embedding = CASE
    WHEN row.embedding = '' THEN []
    ELSE [x IN split(row.embedding, '|') | toFloat(x)]
  END;

LOAD CSV WITH HEADERS FROM 'file:///aletheia_pt_v2/message_topics.csv' AS row
WITH row WHERE toInteger(row.topic_id) <> -1
MATCH (m:Message {id: row.message_id})
MATCH (t:Topic {id: toInteger(row.topic_id)})
MERGE (m)-[r:BELONGS_TO_TOPIC]->(t)
SET
  r.probability = toFloat(row.probability),
  r.rank = toInteger(row.rank);

LOAD CSV WITH HEADERS FROM 'file:///aletheia_pt_v2/community_topics.csv' AS row
MATCH (co:Community {id: toInteger(row.community_id)})
MATCH (t:Topic {id: toInteger(row.topic_id)})
MERGE (co)-[d:DOMINATED_BY]->(t)
SET
  d.share = toFloat(row.share),
  d.message_count = toInteger(row.message_count);
