from src.tools.arxiv_tool import ArxivTool
from src.tools.pdf_parser import PDFParser
from src.tools.section_extractor import SectionExtractor
from src.tools.table_extractor import TableExtractor
from src.tools.equation_extractor import EquationExtractor
from src.tools.figure_extractor import FigureExtractor
from src.tools.paper_validator import PaperValidator


class PaperLoader:

    @staticmethod
    def load(query: str) -> dict:

        if PaperValidator.is_probably_garbage(query):
            raise ValueError(
                f"Invalid paper query: {query}. Please provide a valid arXiv ID, paper URL, or exact paper title."
            )

        papers = ArxivTool.search_paper(
            query=query,
            max_results=3
        )

        if not papers:
            raise ValueError(
                f"No paper found for query: {query}"
            )

        valid_paper = None

        for paper in papers:
            if PaperValidator.validate_result(query, paper):
                valid_paper = paper
                break

        if not valid_paper:
            titles = [p.get("title", "Unknown") for p in papers]

            raise ValueError(
                "Paper search returned results, but none matched your query closely. "
                f"Query: {query}. Found: {titles}. "
                "Please provide an arXiv ID, paper URL, or more exact title."
            )

        pdf_bytes = ArxivTool.fetch_pdf_bytes(
            valid_paper["pdf_url"]
        )

        parsed_pdf = PDFParser.extract_text_blocks(
            pdf_bytes
        )

        sections = SectionExtractor.extract_sections(
            parsed_pdf
        )

        tables = TableExtractor.extract_tables(
            pdf_bytes
        )

        equations = EquationExtractor.extract_equations(
            pdf_bytes
        )

        figures = FigureExtractor.extract_figures(
            pdf_bytes=pdf_bytes,
            paper_id=valid_paper.get("title", query)
        )

        return {
            "query": query,
            "title": valid_paper.get("title", query),
            "authors": valid_paper.get("authors", []),
            "pdf_url": valid_paper.get("pdf_url", ""),
            "pdf_bytes": pdf_bytes,
            "parsed_pdf": parsed_pdf,
            "sections": sections,
            "tables": tables,
            "equations": equations,
            "figures": figures
        }