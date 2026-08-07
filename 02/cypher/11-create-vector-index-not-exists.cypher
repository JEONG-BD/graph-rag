CREATE VECTOR INDEX parent IF NOT EXISTS
FOR (c:Child)
ON c.embedding