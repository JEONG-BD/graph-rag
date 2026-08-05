CALL db.index.vector.queryNodes('pdf', $k, $question_embedding)
YIELD node AS hits, score
RETURN hits.text AS text, score, hits.index AS index