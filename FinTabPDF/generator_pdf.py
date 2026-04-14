import base64
from pathlib import Path

from selenium import webdriver


class PDFGenerator():
    """
    Converts an HTML file to a PDF using Chrome's built-in print-to-PDF
    (Chrome DevTools Protocol — Page.printToPDF).

    The HTML must already contain @media print rules (added by
    DocumentGenerator) so that the page renders to A4 with zero margins.
    """

    # A4 paper size in inches
    _PAPER_WIDTH_IN  = 8.27
    _PAPER_HEIGHT_IN = 11.69

    def __init__(self, pdf_dir: str, driver: webdriver.Chrome) -> None:
        """
        Parameters:
            pdf_dir : Directory where PDF files will be written.
            driver  : Shared Selenium Chrome instance.
        """
        self._pdf_dir = Path(pdf_dir)
        self._driver  = driver

    def __call__(self, doc_id: str, html_path: str) -> str:
        """
        Render html_path to PDF and save as <doc_id>.pdf.

        Parameters:
            doc_id    : Unique document identifier (used as filename stem).
            html_path : Absolute path to the rendered HTML file.

        Returns:
            Absolute path to the written PDF file.
        """
        # Navigate to the HTML file using a file:// URL
        file_url = Path(html_path).as_uri()
        self._driver.get(file_url)

        # Chrome DevTools Protocol: print page to PDF
        result = self._driver.execute_cdp_cmd("Page.printToPDF", {
            "printBackground":  True,
            "paperWidth":       self._PAPER_WIDTH_IN,
            "paperHeight":      self._PAPER_HEIGHT_IN,
            "marginTop":        0,
            "marginBottom":     0,
            "marginLeft":       0,
            "marginRight":      0,
            "scale":            1.0,
            "preferCSSPageSize": True,   # honour @page CSS rules
        })

        pdf_bytes = base64.b64decode(result["data"])
        pdf_path  = self._pdf_dir / f"{doc_id}.pdf"
        pdf_path.write_bytes(pdf_bytes)
        return str(pdf_path)
