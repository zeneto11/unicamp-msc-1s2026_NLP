# Graph V1 — Definitive Schema

Goal:

- represent actors
- represent communication
- preserve diffusion
- preserve reply structure
- support later enrichment

Dataset has:

- 32k messages
- 109 channels
- 5854 users
- ~5k forwards
- ~8k replies

# NODE TYPES

## 1. Channel node

```yaml
label: Channel

id: channel_id

properties:
  channel_id: string

derived:
  total_messages: int
  total_users: int
  active_start: datetime
  active_end: datetime

optional_metrics: total_views
  total_forwards
  total_reactions
```

Source columns:

```text
channel_id
date_parsed
views
n_forwards
reactions
```

Example:

```cypher
(:Channel {
    channel_id:"5159",
    total_messages:2869,
    total_users:4045
})
```

---

## 2. User node

```yaml
label: User

id: user_id

properties:
  user_id: string

derived: total_messages
  channel_count
```

Source:

```text
user_id
channel_id
```

Example:

```cypher
(:User {
    user_id:"1716",
    total_messages:1800,
    channel_count:4
})
```

---

## 3. Message node

```yaml
label: Message

id: message_id

properties:
  message_id: string

  text: text_content

  timestamp: date_parsed

  month: month

  text_length: text_length

  word_count: word_count

  views: views

  reactions: reactions

  forwards: n_forwards

  is_reply: is_reply

  is_forwarded: is_forwarded
```

Source columns:

```text
message_id
text_content
date_parsed
month
views
reactions
n_forwards
text_length
word_count
is_reply
is_forwarded
```

Example:

```cypher
(:Message {
    message_id:"_357",
    timestamp:"2023-01-15",
    views:1200,
    reactions:33
})
```

# RELATION TYPES

## 1. User authored message

Mandatory relation.

```yaml
(User)-[:POSTED]->(Message)
```

Construction:

```text
user_id
message_id
```

Example:

```cypher
(u:User)-[:POSTED]->(m:Message)
```

Meaning:

User created this message.

---

## 2. Message belongs to channel

Mandatory.

```yaml
(Message)-[:IN_CHANNEL]->(Channel)
```

Construction:

```text
message_id
channel_id
```

Example:

```cypher
(m)-[:IN_CHANNEL]->(c)
```

Meaning:

Message appeared in channel.

---

## 3. Aggregated participation edge

Not mandatory but strongly recommended.

Build AFTER all messages.

```yaml
(User)-[:ACTIVE_IN]->(Channel)
```

Properties:

```yaml
messages_count
total_views
total_reactions
total_forwards
first_seen
last_seen
```

Computed from:

group by:

```python
(user_id, channel_id)
```

Aggregation:

```python
count(messages)

sum(views)

sum(reactions)

sum(n_forwards)
```

This corresponds to user-channel activity network already observed in report .

---

## 4. Reply graph

Very important.

Dataset:

```text
reply_to
reply_to_channel
```

Primary edge:

```yaml
(Message)-[:REPLIES_TO]->(Message)
```

Construction:

```python
source =
current message_id

target =
reply_to
```

Properties:

```yaml
reply_timestamp
same_channel: bool
```

Fallback:

If target message absent:

```yaml
(Message)-[:REPLIED_INTO]->(Channel)
```

using:

```text
reply_to_channel
```

Because reply recovery is incomplete (~51 reply channels recovered) .

---

## 5. Forward structure

Dataset:

```text
forward_from
forward_from_channel
```

V1 uses:

```yaml
(Message)-[:FORWARDED_FROM]->(Channel)
```

Construction:

For each forwarded message:

```python
source =
message_id

target =
forward_from_channel
```

Example:

Dataset:

```text
message_id = m100

channel_id = B

forward_from_channel = A
```

Graph:

```text
m100 ----FORWARDED_FROM----> Channel_A

m100 ----IN_CHANNEL-------> Channel_B
```

Meaning:

- message `m100` exists in channel `B`
- message `m100` originated from channel `A`

---

# Final V1 Overview

## Topology

```text
(User)
   |
 POSTED
   |
   v

(Message)
   |
   +----------------+
   |                |
IN_CHANNEL      REPLIES_TO
   |                |
   v                v

(Channel)      (Message)

(User)
   |
ACTIVE_IN
   |
   v

(Channel)

(Message)
    |
FORWARDED_FROM
    |
    v
(Channel)
```

## Suggested config object (implementation-ready)

```yaml
graph_name: telegram_v1

nodes:
  Channel:
    key: channel_id

  User:
    key: user_id

  Message:
    key: message_id

edges:
  POSTED:
    source: user_id
    target: message_id

  IN_CHANNEL:
    source: message_id
    target: channel_id

  ACTIVE_IN:
    aggregate:
      by:
        - user_id
        - channel_id

      metrics:
        - count_messages
        - sum_views
        - sum_reactions
        - sum_forwards

  REPLIES_TO:
    source: message_id
    target: reply_to

  REPLIED_INTO:
    source: message_id
    target: reply_to_channel

  FORWARDED_FROM:
    source: message_id
    target: forward_from_channel
```
