LOAD CSV WITH HEADERS FROM 'file:///aletheia_pt_v1/posted.csv' AS row
MATCH (u:User {id: row.user_id})
MATCH (m:Message {id: row.message_id})
MERGE (u)-[:POSTED {}]->(m);

LOAD CSV WITH HEADERS FROM 'file:///aletheia_pt_v1/in_channel.csv' AS row
MATCH (m:Message {id: row.message_id})
MATCH (c:Channel {id: row.channel_id})
MERGE (m)-[:IN_CHANNEL {}]->(c);

LOAD CSV WITH HEADERS FROM 'file:///aletheia_pt_v1/replies_to.csv' AS row
MATCH (m:Message {id: row.message_id})
MERGE (target:Message {id: row.target_message_id})
ON CREATE SET
  target.is_stub = true
MERGE (m)-[:REPLIES_TO {}]->(target);

LOAD CSV WITH HEADERS FROM 'file:///aletheia_pt_v1/replied_into.csv' AS row
MATCH (m:Message {id: row.message_id})
MATCH (c:Channel {id: row.channel_id})
MERGE (m)-[:REPLIED_INTO {}]->(c);

LOAD CSV WITH HEADERS FROM 'file:///aletheia_pt_v1/forwarded_from.csv' AS row
MATCH (m:Message {id: row.message_id})
MATCH (c:Channel {id: row.channel_id})
MERGE (m)-[:FORWARDED_FROM {}]->(c);

LOAD CSV WITH HEADERS FROM 'file:///aletheia_pt_v1/active_in.csv' AS row
MATCH (u:User {id: row.user_id})
MATCH (c:Channel {id: row.channel_id})
MERGE (u)-[r:ACTIVE_IN {}]->(c)
SET
  r.total_messages = toInteger(row.total_messages),
  r.total_views = toFloat(row.total_views),
  r.total_reactions = toInteger(row.total_reactions),
  r.total_forwards = toFloat(row.total_forwards);