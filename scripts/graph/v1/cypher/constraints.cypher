CREATE CONSTRAINT channel_id IF NOT EXISTS
FOR (c:Channel)
REQUIRE c.id IS UNIQUE;

CREATE CONSTRAINT user_id IF NOT EXISTS
FOR (u:User)
REQUIRE u.id IS UNIQUE;

CREATE CONSTRAINT message_id IF NOT EXISTS
FOR (m:Message)
REQUIRE m.id IS UNIQUE;

CREATE INDEX message_month IF NOT EXISTS
FOR (m:Message)
ON (m.month);

CREATE INDEX message_date IF NOT EXISTS
FOR (m:Message)
ON (m.date_parsed);