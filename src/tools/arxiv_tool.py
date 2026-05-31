import re
import json
import requests
from pathlib import Path

import arxiv


CACHE_FILE = "data/url_cache.json"

VENUE_PATTERNS = {
    "openreview.net": lambda url: url.replace("/forum?id=", "/pdf?id="),
    "aclanthology.org": lambda url: url if url.endswith(".pdf") else url.rstrip("/") + ".pdf",
    "proceedings.mlr.press": lambda url: url,
    "openaccess.thecvf.com": lambda url: url.replace("/html/", "/papers/").replace(".html", ".pdf") if ".html" in url else url,
    "proceedings.neurips.cc": lambda url: url.replace("/hash/", "/file/").replace("-Abstract.html", "-Paper.pdf") if "Abstract" in url else url,
}


class ArxivTool:

    @staticmethod
    def _load_cache():
        if Path(CACHE_FILE).exists():
            with open(CACHE_FILE, "r") as f:
                return json.load(f)
        return {}

    @staticmethod
    def _save_cache(cache):
        Path(CACHE_FILE).parent.mkdir(parents=True, exist_ok=True)
        with open(CACHE_FILE, "w") as f:
            json.dump(cache, f, indent=2)

    @staticmethod
    def sanitize_filename(name):
        name = re.sub(r"[^\w\s-]", "", name)
        name = re.sub(r"\s+", "_", name)
        return name[:100]

    @staticmethod
    def _looks_like_arxiv_id(query):
        return re.match(r"^\d{4}\.\d{4,5}(v\d+)?$", query.strip()) is not None

    @staticmethod
    def _extract_arxiv_id(query):
        match = re.search(r"\b\d{4}\.\d{4,5}(v\d+)?\b", query)
        if match:
            return match.group(0)
        return None

    @staticmethod
    def _is_pdf_url(url):
        return url.lower().endswith(".pdf")

    @staticmethod
    def _resolve_venue_pdf_url(item):
        external_ids = item.get("externalIds", {})

        acl_id = external_ids.get("ACL")
        if acl_id:
            return f"https://aclanthology.org/{acl_id}.pdf"

        url = item.get("url", "")
        if not url:
            return None

        for domain, resolver in VENUE_PATTERNS.items():
            if domain in url:
                try:
                    resolved = resolver(url)
                    head = requests.head(
                        resolved,
                        timeout=10,
                        allow_redirects=True,
                        headers={"User-Agent": "Mozilla/5.0"}
                    )

                    if head.status_code == 200:
                        content_type = head.headers.get("content-type", "")
                        if "pdf" in content_type.lower() or resolved.endswith(".pdf"):
                            return resolved

                except Exception:
                    pass

        try:
            response = requests.get(
                url,
                timeout=15,
                headers={"User-Agent": "Mozilla/5.0"}
            )

            if response.status_code == 200:
                pdf_links = re.findall(
                    r'href=["\']([^"\']*\.pdf)["\']',
                    response.text
                )

                for link in pdf_links:
                    if link.startswith("http"):
                        return link

                    if link.startswith("/"):
                        base = re.match(r"(https?://[^/]+)", url)
                        if base:
                            return base.group(1) + link

        except Exception:
            pass

        return None

    @staticmethod
    def _search_semantic_scholar(query, max_results):
        try:
            url = "https://api.semanticscholar.org/graph/v1/paper/search"

            params = {
                "query": query,
                "limit": max_results,
                "fields": "title,authors,externalIds,url,venue,year,openAccessPdf"
            }

            response = requests.get(
                url,
                params=params,
                timeout=20,
                headers={"User-Agent": "Mozilla/5.0"}
            )

            response.raise_for_status()

            data = response.json()

            papers = []

            for item in data.get("data", []):
                title = item.get("title", "Unknown")

                authors = [
                    author.get("name", "")
                    for author in item.get("authors", [])
                    if author.get("name")
                ]

                external_ids = item.get("externalIds", {}) or {}

                pdf_url = None

                arxiv_id = external_ids.get("ArXiv")
                if arxiv_id:
                    pdf_url = f"https://arxiv.org/pdf/{arxiv_id}.pdf"

                if not pdf_url:
                    open_access_pdf = item.get("openAccessPdf") or {}
                    pdf_url = open_access_pdf.get("url")

                if not pdf_url:
                    pdf_url = ArxivTool._resolve_venue_pdf_url(item)

                if pdf_url:
                    papers.append(
                        {
                            "title": title,
                            "authors": authors,
                            "pdf_url": pdf_url,
                            "source": "semantic_scholar"
                        }
                    )

            return papers

        except Exception as e:
            print("Semantic Scholar search failed:", e)
            return []

    @staticmethod
    def _search_arxiv_api(query, max_results):
        try:
            client = arxiv.Client()

            search = arxiv.Search(
                query=query,
                max_results=max_results,
                sort_by=arxiv.SortCriterion.Relevance
            )

            papers = []

            for result in client.results(search):
                papers.append(
                    {
                        "title": result.title,
                        "authors": [author.name for author in result.authors],
                        "pdf_url": result.pdf_url,
                        "source": "arxiv"
                    }
                )

            return papers

        except Exception as e:
            print("arXiv fallback search failed:", e)
            return []

    @staticmethod
    def _resolve_url_query(query):
        url = query.strip()

        for domain, resolver in VENUE_PATTERNS.items():
            if domain in url:
                try:
                    return resolver(url)
                except Exception:
                    return url

        return url

    @staticmethod
    def search_paper(query, max_results=1):
        cache = ArxivTool._load_cache()

        clean_query = query.strip()
        cache_key = clean_query.lower()

        extracted_arxiv_id = ArxivTool._extract_arxiv_id(clean_query)

        if extracted_arxiv_id:
            pdf_url = f"https://arxiv.org/pdf/{extracted_arxiv_id}.pdf"

            cache[cache_key] = pdf_url
            cache[extracted_arxiv_id.lower()] = pdf_url
            ArxivTool._save_cache(cache)

            return [
                {
                    "title": extracted_arxiv_id,
                    "authors": [],
                    "pdf_url": pdf_url,
                    "source": "arxiv_id"
                }
            ]

        if cache_key in cache:
            return [
                {
                    "title": clean_query,
                    "authors": [],
                    "pdf_url": cache[cache_key],
                    "source": "cache"
                }
            ]

        if clean_query.startswith("http"):
            pdf_url = ArxivTool._resolve_url_query(clean_query)

            cache[cache_key] = pdf_url
            ArxivTool._save_cache(cache)

            return [
                {
                    "title": clean_query,
                    "authors": [],
                    "pdf_url": pdf_url,
                    "source": "url"
                }
            ]

        papers = ArxivTool._search_semantic_scholar(
            clean_query,
            max_results=max_results
        )

        if not papers:
            papers = ArxivTool._search_arxiv_api(
                clean_query,
                max_results=max_results
            )

        if papers:
            for paper in papers:
                title_key = paper["title"].strip().lower()
                cache[title_key] = paper["pdf_url"]

            cache[cache_key] = papers[0]["pdf_url"]

            ArxivTool._save_cache(cache)

        return papers

    @staticmethod
    def fetch_pdf_bytes(pdf_url):
        headers = {
            "User-Agent": "Mozilla/5.0"
        }

        response = requests.get(
            pdf_url,
            timeout=30,
            headers=headers,
            allow_redirects=True
        )

        response.raise_for_status()

        content_type = response.headers.get("content-type", "").lower()

        if "pdf" not in content_type and not pdf_url.lower().endswith(".pdf"):
            raise ValueError(
                f"URL did not return a PDF: {pdf_url}"
            )

        return response.content

    @staticmethod
    def search_and_fetch(query, max_results=1):
        papers = ArxivTool.search_paper(
            query=query,
            max_results=max_results
        )

        if not papers:
            raise ValueError(
                f"No paper found for query: {query}"
            )

        paper = papers[0]

        pdf_bytes = ArxivTool.fetch_pdf_bytes(
            paper["pdf_url"]
        )

        return paper, pdf_bytes