from pathlib import Path
from typing import Any
from IPython.display import HTML, display
from neo4j_viz.neo4j import from_neo4j
from neo4j import Driver, GraphDatabase, Result, RoutingControl
from settings import get_settings
from pathlib import Path
from playwright.async_api import async_playwright

settings = get_settings()
print(settings.neo4j_url)


class Neo4jCustomClient:
    """Neo4j 연결과 Cypher 파일 실행을 관리하는 클라이언트."""

    def __init__(
        self,
        # uri: str|None = None,
        # user: str|None = None ,
        # password: str|None = None,
        cypher_dir: Path | None = None,
    ) -> None:
        self.driver: Driver = GraphDatabase.driver(
            uri=settings.neo4j_url,
            auth=(settings.neo4j_user, settings.neo4j_password),
        )

        self.cypher_dir = (
            cypher_dir if cypher_dir is not None else Path.cwd() / "cypher"
        )

    def verify_connectivity(self) -> bool:
        """Neo4j 서버 연결 상태를 확인합니다."""
        try:
            self.driver.verify_connectivity()
            return True
        except Exception as e:
            raise ConnectionError(f"Neo4j 연결에 실패했습니다.: {e}") from e

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
            raise ValueError(f"Cypher 파일이 비어 있습니다: {query_path}")

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

    def get_schema(self) -> str:
        structured_schema = self._get_structured_schema()

        def _format_props(props: list[dict[str, Any]]) -> str:
            return ", ".join([f"{prop['property']}: {prop['type']}" for prop in props])

        formatted_node_props = [
            f"{label} {{{_format_props(props)}}}"
            for label, props in structured_schema["node_props"].items()
        ]

        formatted_rel_props = [
            f"{rel_type} {{{_format_props(props)}}}"
            for rel_type, props in structured_schema["rel_props"].items()
        ]

        formatted_rels = [
            f"(:{element['start']})-[:{element['type']}]->(:{element['end']})"
            for element in structured_schema["relationships"]
        ]

        return "\n".join(
            [
                "Node properties:",
                "\n".join(formatted_node_props),
                "Relationship properties:",
                "\n".join(formatted_rel_props),
                "The relationships:",
                "\n".join(formatted_rels),
            ]
        )

    def _get_structured_schema(self) -> dict[str, Any]:
        node_labels_response = self.execute_query("node-properties")
        node_properties = [
            data["output"] for data in [r.data() for r in node_labels_response.records]
        ]

        rel_properties_query_response = self.execute_query("relation-properties")
        rel_properties = [
            data["output"]
            for data in [r.data() for r in rel_properties_query_response.records]
        ]

        rel_query_response = self.execute_query("relation")
        relationships = [
            data["output"] for data in [r.data() for r in rel_query_response.records]
        ]

        return {
            "node_props": {el["labels"]: el["properties"] for el in node_properties},
            "rel_props": {el["type"]: el["properties"] for el in rel_properties},
            "relationships": relationships,
        }

    def _get_query_path(self, query_name: str) -> Path:
        return self.cypher_dir / f"{query_name}.cypher"

    def visualize_graph(self, query: str) -> HTML:
        """Graph를 노트북 화면에 시각화합니다."""
        graph = self.execute_query(
            query,
            routing_=RoutingControl.READ,
            result_transformer_=Result.graph,
        )

        rendered_html = from_neo4j(graph).render()
        display(rendered_html)

        return rendered_html

    def save_graph_html(
        self,
        query_name: str,
        **kwargs: Any,
    ) -> Path:
        """Cypher 파일을 실행하고 그래프를 HTML 파일로 저장합니다."""
        graph = self.execute_query(
            query_name,
            routing_=RoutingControl.READ,
            result_transformer_=Result.graph,
            **kwargs,
        )

        query_path = self._get_query_path(query_name)

        image_dir = query_path.parent.parent / "image"
        image_dir.mkdir(parents=True, exist_ok=True)

        output_path = image_dir / f"{query_path.stem}.html"

        rendered_html = from_neo4j(graph).render()

        output_path.write_text(
            rendered_html.data,
            encoding="utf-8",
        )

        return output_path

    async def save_graph_png(
            self,
            html_path: str | Path,
    ) -> Path:
        html_path = Path(html_path)
        png_path = html_path.with_suffix(".png")

        async with async_playwright() as p:
            browser = await p.chromium.launch()

            page = await browser.new_page(
                viewport={
                    "width": 1920,
                    "height": 1080,
                }
            )

            await page.goto(html_path.resolve().as_uri())
            await page.wait_for_timeout(2000)

            await page.screenshot(
                path=str(png_path),
                full_page=True,
            )

            await browser.close()

        return png_path