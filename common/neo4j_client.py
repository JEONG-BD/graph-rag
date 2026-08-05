from pathlib import Path
from typing import Any

from neo4j import Driver, GraphDatabase


class Neo4jClient:
    """Neo4j 연결과 Cypher 파일 실행을 관리하는 클라이언트."""

    def __init__(
        self,
        uri: str,
        user: str,
        password: str,
        cypher_dir: Path | None = None,
    ) -> None:
        self.driver: Driver = GraphDatabase.driver(
            uri,
            auth=(user, password),
        )

        self.cypher_dir = (
            cypher_dir
            if cypher_dir is not None
            else Path.cwd() / "cypher"
        )

    def verify_connectivity(self) -> bool:
        """Neo4j 서버 연결 상태를 확인합니다."""
        try:
            self.driver.verify_connectivity()
            return True
        except Exception as e:
            raise ConnectionError(
                f"Neo4j 연결에 실패했습니다.: {e}"
            ) from e

    def _load_query(self, query_name: str) -> str:
        """
        Cypher 쿼리 파일을 읽어 문자열로 반환합니다.

        Args:
            query_name: 확장자를 제외한 Cypher 파일 이름.

        Returns:
            파일에서 읽은 Cypher 쿼리 문자열.

        Raises:
            FileNotFoundError: 지정한 Cypher 파일이 존재하지 않는 경우.
            ValueError: Cypher 파일이 비어 있는 경우.
        """
        query_path = self.cypher_dir / f"{query_name}.cypher"

        try:
            query = query_path.read_text(encoding="utf-8").strip()
        except FileNotFoundError as e:
            raise FileNotFoundError(
                f"Cypher 파일을 찾을 수 없습니다: {query_path}"
            ) from e

        if not query:
            raise ValueError(
                f"Cypher 파일이 비어 있습니다: {query_path}"
            )

        return query

    def execute_query(
        self,
        query_name: str,
        **kwargs: Any,
    ):
        """Cypher 파일을 읽어 Neo4j에서 실행합니다."""
        query = self._load_query(query_name)

        return self.driver.execute_query(
            query,
            **kwargs,
        )


    def execute_query_file(self, query_name: str, **kwargs):
        query = self._load_query(query_name)
        return self.driver.execute_query(query, **kwargs)

    def close(self) -> None:
        """Neo4j 드라이버 연결을 종료합니다."""
        self.driver.close()