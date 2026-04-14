from pathlib import Path
from typing import List

from htmltree import (HtmlElement, Body, Head, Html, Meta, Style, Title,
                      Table, Tr, Th, Td, Span)


# Print-media CSS injected after htmltree render
_PRINT_CSS = (
    '<style>'
    '@media print {'
    '  @page { size: A4 portrait; margin: 0; }'
    '  body  { margin: 0 !important; padding: 0 !important; }'
    '}'
    '</style>'
)


class DocumentGenerator():
    """Creates HTML documents from table data. Optimised for A4 PDF output."""

    def __init__(self, html_dir: str) -> None:
        self._html_dir = html_dir

    def __call__(self, doc_id: str, table: List[List[dict]], theme: dict) -> str:
        """
        Render an HTML document and return its absolute file path.

        Parameters:
            doc_id  : Unique document identifier.
            table   : 2-D list of cell dicts from TableGenerator.
            theme   : CSS theme dict from ThemeGenerator.

        Returns:
            Absolute path to the written HTML file.
        """
        return self._create_html_document(doc_id, table, theme)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _create_html_document(self, doc_id, table, theme):
        html_table = self._create_html_table(table)
        doc_head   = self._create_html_head(doc_id, theme)
        doc_body   = Body(html_table)
        doc        = Html(doc_head, doc_body, lang="en")

        # Use the known OS path directly — renderToFile returns a file:// URL
        # which can't be used directly as a pathlib.Path.
        actual_path = Path(self._html_dir) / f"{doc_id}.html"
        doc.renderToFile(str(actual_path))

        # htmltree's Style(**dict) doesn't support @media rules,
        # so we inject the print CSS directly into the rendered file.
        self._inject_print_css(actual_path)

        return str(actual_path)

    def _inject_print_css(self, file_path) -> None:
        """Append @media print rules to the <head> of the rendered HTML."""
        p = Path(file_path)
        html = p.read_text(encoding='utf-8')
        if '</head>' in html:
            html = html.replace('</head>', f'{_PRINT_CSS}</head>', 1)
        else:
            html = _PRINT_CSS + html
        p.write_text(html, encoding='utf-8')

    def _create_html_head(self, doc_id, theme):
        charset_meta  = Meta(charset="utf-8")
        viewport_meta = Meta(
            name="viewport",
            content="width=device-width, initial-scale=1")
        style = Style(**theme)
        title = Title(doc_id)
        return Head(charset_meta, viewport_meta, style, title)

    def _create_html_table(self, table):
        html_table = Table(id="t0")

        for i, row in enumerate(table):
            table_row = Tr(id=f"t0:r{i}")

            for j, col in enumerate(row):
                if col['type'] == "HEADER":
                    cell = Th(
                        id=f"t0:r{i}:c{j}",
                        colspan=col['colspan'],
                        scope=col['scope'])
                else:
                    cell = Td(
                        id=f"t0:r{i}:c{j}",
                        colspan=col['colspan'])

                if col['classes']:
                    cell.A.update({'class': col['classes']})

                for k, word in enumerate(col['content'].split()):
                    cell.C.extend([Span(word, id=f"t0:r{i}:c{j}:w{k}"), " "])

                table_row.C.append(cell)

            html_table.C.append(table_row)

        return html_table
