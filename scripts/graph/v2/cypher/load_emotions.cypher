LOAD CSV WITH HEADERS FROM 'file:///aletheia_pt_v2/message_emotions.csv' AS row
MATCH (m:Message {id: row.message_id})
SET
  m.anger_score = toFloat(row.anger_score),
  m.anticipation_score = toFloat(row.anticipation_score),
  m.disgust_score = toFloat(row.disgust_score),
  m.fear_score = toFloat(row.fear_score),
  m.joy_score = toFloat(row.joy_score),
  m.sadness_score = toFloat(row.sadness_score),
  m.surprise_score = toFloat(row.surprise_score),
  m.trust_score = toFloat(row.trust_score),
  m.positive_score = toFloat(row.positive_score),
  m.negative_score = toFloat(row.negative_score),
  m.dominant_emotion = row.dominant_emotion;
