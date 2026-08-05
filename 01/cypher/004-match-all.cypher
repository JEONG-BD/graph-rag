MATCH (c:Chunk) WHERE c.index = 0
RETURN c.embedding, c.text