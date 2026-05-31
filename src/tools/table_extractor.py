import fitz
import re


class TableExtractor:

    @staticmethod
    def _clean_cell(text):
        if not text:
            return ""
        text = re.sub(r"\s*\n\s*", " ", text)
        return text.strip()

    @staticmethod
    def _is_garbage_table(rows):
        if not rows:
            return True

        total_cells = sum(len(row) for row in rows)

        if total_cells == 0:
            return True

        flat_cells = [
            (cell or "").strip()
            for row in rows
            for cell in row
        ]

        empty_cells = sum(
            1 for cell in flat_cells
            if not cell
        )

        if empty_cells / total_cells > 0.75:
            return True

        meaningful = sum(
            1 for cell in flat_cells
            if len(cell) > 2
        )

        if meaningful < 4:
            return True

        max_cols = max(len(r) for r in rows)

        # Reject weird attention maps / token matrices
        if max_cols > 20:
            return True

        short_cells = sum(
            1 for cell in flat_cells
            if len(cell) <= 2
        )

        if short_cells / total_cells > 0.60:
            return True

        joined = " ".join(flat_cells).lower()

        special_token_count = (
            joined.count("<eos>")
            + joined.count("<pad>")
            + joined.count("<bos>")
        )

        if special_token_count > 3:
            return True

        return False

    @staticmethod
    def _extract_header(table):
        header_names = []
        try:
            hdr = table.header
            if hdr and hdr.names:
                header_names = [TableExtractor._clean_cell(n) for n in hdr.names]
        except Exception:
            pass
        return header_names

    @staticmethod
    def _col_widths(rows):
        if not rows:
            return []
        ncols = max(len(r) for r in rows)
        widths = [0] * ncols
        for row in rows:
            for i, cell in enumerate(row):
                widths[i] = max(widths[i], len(cell or ""))
        return widths

    @staticmethod
    def _render_row(row, widths):
        parts = []
        for i, cell in enumerate(row):
            w = widths[i] if i < len(widths) else 10
            parts.append((cell or "").ljust(w))
        return " | ".join(parts)

    @staticmethod
    def _render_divider(widths):
        return "-+-".join("-" * w for w in widths)

    @staticmethod
    def _format_table(header, rows):
        all_rows = []
        if header:
            all_rows.append(header)
        all_rows.extend(rows)

        widths = TableExtractor._col_widths(all_rows)
        if not widths:
            return ""

        lines = []
        if header:
            lines.append(TableExtractor._render_row(header, widths))
            lines.append(TableExtractor._render_divider(widths))
            for row in rows:
                lines.append(TableExtractor._render_row(row, widths))
        else:
            for row in all_rows:
                lines.append(TableExtractor._render_row(row, widths))

        return "\n".join(lines)

    @staticmethod
    def extract_tables(pdf_source):
        if isinstance(pdf_source, bytes):
            doc = fitz.open(stream=pdf_source, filetype="pdf")
        else:
            doc = fitz.open(pdf_source)

        results = []

        for page_num in range(len(doc)):
            page = doc[page_num]

            try:
                tabs = page.find_tables()
            except Exception:
                continue

            for table in tabs.tables:
                try:
                    raw_rows = table.extract()
                except Exception:
                    continue

                if not raw_rows:
                    continue

                cleaned_rows = [
                    [TableExtractor._clean_cell(cell) for cell in row]
                    for row in raw_rows
                ]

                if TableExtractor._is_garbage_table(cleaned_rows):
                    continue

                header = TableExtractor._extract_header(table)

                if header and all(h == "" for h in header):
                    header = []

                if header:
                    data_rows = cleaned_rows
                else:
                    data_rows = cleaned_rows[1:]
                    first_row = cleaned_rows[0]
                    if any(c.strip() for c in first_row):
                        header = first_row

                text = TableExtractor._format_table(header, data_rows)

                results.append({
                    "page": page_num,
                    "bbox": tuple(table.bbox),
                    "header": header,
                    "rows": data_rows,
                    "text": text
                })

        return results