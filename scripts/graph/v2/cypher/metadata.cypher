MERGE (g:GraphBuild {name: 'aletheia_pt_v2'})
SET
  g.dataset = 'aletheia_clean_pt.csv',
  g.version = 'v2',
  g.description = 'Portuguese Aletheia communities, topics, similarity and emotion layer',
  g.extends = 'aletheia_pt_v1',
  g.created_at = datetime();
