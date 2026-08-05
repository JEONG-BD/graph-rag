WITH $chunks as chunks, range(0, size($chunks)) AS index
UNWIND index AS i
WITH i, chunks[i] AS chunk, $embeddings[i] AS embedding
  MERGE (c:Chunk {index: i})
  SET c.text = chunk, c.embedding = embedding
