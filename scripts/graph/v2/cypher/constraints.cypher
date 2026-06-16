CREATE CONSTRAINT community_id IF NOT EXISTS
FOR (c:Community)
REQUIRE c.id IS UNIQUE;

CREATE CONSTRAINT topic_id IF NOT EXISTS
FOR (t:Topic)
REQUIRE t.id IS UNIQUE;

CREATE INDEX topic_label IF NOT EXISTS
FOR (t:Topic)
ON (t.label);

CREATE INDEX message_dominant_emotion IF NOT EXISTS
FOR (m:Message)
ON (m.dominant_emotion);
