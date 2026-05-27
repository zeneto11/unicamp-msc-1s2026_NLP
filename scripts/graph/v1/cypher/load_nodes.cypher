LOAD CSV WITH HEADERS FROM 'file:///aletheia_pt_v1/channels.csv' AS row
MERGE (c:Channel {id: row.id})
SET
  c.total_messages = toInteger(row.total_messages),
  c.total_users = toInteger(row.total_users),
  c.active_start = row.active_start,
  c.active_end = row.active_end,
  c.total_views = toFloat(row.total_views),
  c.total_forwards = toFloat(row.total_forwards),
  c.total_reactions = toInteger(row.total_reactions),
  c.is_dataset_channel = toBoolean(row.is_dataset_channel),
  c.is_forward_source = toBoolean(row.is_forward_source),
  c.is_reply_source = toBoolean(row.is_reply_source);

LOAD CSV WITH HEADERS FROM 'file:///aletheia_pt_v1/users.csv' AS row
MERGE (u:User {id: row.id})
SET
  u.total_messages = toInteger(row.total_messages),
  u.channel_count = toInteger(row.channel_count);

LOAD CSV WITH HEADERS FROM 'file:///aletheia_pt_v1/messages.csv' AS row
MERGE (m:Message {id: row.id})
SET
  m.text_content = row.text_content,
  m.date_parsed = row.date_parsed,
  m.month = row.month,
  m.text_length = toInteger(row.text_length),
  m.word_count = toInteger(row.word_count),
  m.views = toFloat(row.views),
  m.reactions = toInteger(row.reactions),
  m.n_forwards = toFloat(row.n_forwards),
  m.is_reply = toBoolean(row.is_reply),
  m.is_forwarded = toBoolean(row.is_forwarded);