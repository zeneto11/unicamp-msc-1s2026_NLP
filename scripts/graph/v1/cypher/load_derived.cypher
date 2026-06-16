LOAD CSV WITH HEADERS FROM 'file:///aletheia_pt_v1/interacts_with.csv' AS row
MATCH (a:Channel {id: row.source})
MATCH (b:Channel {id: row.target})
MERGE (a)-[r:INTERACTS_WITH]->(b)
SET
  r.shared_users_count = toInteger(row.shared_users_count),
  r.forward_count       = toInteger(row.forward_count),
  r.reply_count         = toInteger(row.reply_count),
  r.interaction_count   = toInteger(row.interaction_count),
  r.interaction_weight  = toFloat(row.interaction_weight),
  r.has_shared_user_signal = toBoolean(row.has_shared_user_signal),
  r.has_forward_signal     = toBoolean(row.has_forward_signal),
  r.has_reply_signal       = toBoolean(row.has_reply_signal);
