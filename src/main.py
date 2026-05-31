from src.tools.paper_laoder import PaperLoader
from src.agents.image_agent import ImageAgent


def main():

    paper = PaperLoader.load("1706.03762")

    print(f"Found {len(paper['figures'])} figures")

    agent = ImageAgent()

    result = agent.run(
        figures=paper["figures"],
        user_question="Explain the architecture diagram in this paper",
        create_gif=True
    )

    for fig in result.figures:
        print("\n" + "=" * 80)
        print(f"Page {fig.page} | Figure {fig.figure_index}")
        print("=" * 80)
        print(fig.explanation)

    print("\nGIF Path:", result.gif_path)


if __name__ == "__main__":
    main()

# from tools.arxiv_tool import ArxivTool
# from tools.pdf_parser import PDFParser
# from tools.section_extractor import SectionExtractor
# from tools.table_extractor import TableExtractor
# from tools.equation_extractor import EquationExtractor
# from agents.summarizer_agent import SummarizerAgent
# import numpy as np



# def main():

#     # query = "1706.03762"

#     # print("\nSEARCHING PAPER...\n")

#     # papers = ArxivTool.search_paper(
#     #     query=query,
#     #     max_results=1
#     # )

#     # if not papers:
#     #     print("No papers found.")
#     #     return

#     # paper = papers[0]

#     # # print("FOUND PAPER:\n")
#     # # print("Title:", paper["title"])
#     # # print("Authors:", ", ".join(paper["authors"]))
#     # # print()

#     # print("FETCHING PDF...\n")

#     # pdf_bytes = ArxivTool.fetch_pdf_bytes(paper["pdf_url"])

#     # print("PDF FETCHED SUCCESSFULLY\n")
#     # print()

#     # pages_data = PDFParser.extract_text_blocks(pdf_bytes)

#     # # print(type(pages_data))
#     # print()
#     # print("PDF PARSED SUCCESSFULLY\n")


#     # font_sizes = np.array([b["font_size"] for b in pages_data["blocks"]])
#     # sorted_sizes = np.sort(font_sizes)
#     # for b in pages_data["blocks"]:
#     #     rank = np.searchsorted(sorted_sizes, b["font_size"]) / len(sorted_sizes)
#     #     b["font_rank"] = rank

#     # # for b in pages_data["blocks"]:
#     # #     if SectionExtractor.is_heading(b):
#     # #         print(f"page={b['page']} y={b['y']:.1f} font_rank={b['font_rank']:.3f} bold={b['is_bold']} | '{b['text'][:80]}'")

#     # sections = SectionExtractor.extract_sections(pages_data)

#     # print("\nDETECTED HEADINGS:\n")

#     # # for heading in sections.keys():
#     # #     print(heading)

#     # print("\nEXTRACTED SECTIONS:\n")

#     # # for title, content in sections.items():
#     # #     print(title)
#     # #     print("-" * 50)
#     # #     print(content[:1500])
#     # #     print("\n")

#     # print("\nEXTRACTED TABLES:\n")

#     # tables = TableExtractor.extract_tables(pdf_bytes)
#     # print(f"Found {len(tables)} table(s)\n")
#     # # for i, table in enumerate(tables):
#     # #     print(f"Table {i + 1} | page={table['page']} | bbox={table['bbox']}")
#     # #     print(table["text"])
#     # #     print("\n")

#     # print("\nEXTRACTED EQUATIONS:\n")

#     # equations = EquationExtractor.extract_equations(pdf_bytes)
#     # # print(f"Found {len(equations)} equation(s)\n")
#     # # for i, eq in enumerate(equations):
#     # #     print(f"Equation {i + 1} | page={eq['page']} | score={eq['score']} | bbox={eq['bbox']}")
#     # #     print(eq["text"])
#     # #     print("\n")
#     # # print("\nRUNNING SUMMARIZER AGENT...\n")

#     agent = SummarizerAgent()
#     result = agent.run("1706.03762")
#     print(result.model_dump_json(indent=2))


# if __name__ == "__main__":

#     main()