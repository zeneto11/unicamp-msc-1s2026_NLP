MERGE (g:GraphBuild {name: 'aletheia_pt_v1'})
SET
  g.dataset = 'aletheia_clean_pt.csv',
  g.version = 'v1',
  g.description = 'Portuguese Aletheia Telegram graph',
  g.created_at = datetime();