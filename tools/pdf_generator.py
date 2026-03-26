"""Genera PDFs desde los CVs HTML usando Edge"""
import json
import base64
import time
import os
from selenium import webdriver
from selenium.webdriver.edge.options import Options

def html_to_pdf(html_path, pdf_path):
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")

    driver = webdriver.Edge(options=options)
    try:
        abs_path = os.path.abspath(html_path)
        driver.get(f"file:///{abs_path}")
        time.sleep(2)

        # Usar CDP para imprimir a PDF
        result = driver.execute_cdp_cmd("Page.printToPDF", {
            "printBackground": True,
            "paperWidth": 8.27,   # A4 en pulgadas
            "paperHeight": 11.69,
            "marginTop": 0,
            "marginBottom": 0,
            "marginLeft": 0,
            "marginRight": 0,
        })

        pdf_data = base64.b64decode(result["data"])
        with open(pdf_path, "wb") as f:
            f.write(pdf_data)
        print(f"PDF generado: {pdf_path}")
    finally:
        driver.quit()

if __name__ == "__main__":
    base = os.path.dirname(os.path.abspath(__file__))

    # CV en español
    html_es = os.path.join(base, "cv.html")
    pdf_es = os.path.join(base, "cv.pdf")

    # CV en inglés
    html_en = os.path.join(base, "cv_en.html")
    pdf_en = os.path.join(base, "cv_en.pdf")

    if os.path.exists(html_es):
        html_to_pdf(html_es, pdf_es)
    else:
        print(f"No encontrado: {html_es}")

    if os.path.exists(html_en):
        html_to_pdf(html_en, pdf_en)
    else:
        print(f"No encontrado: {html_en}")

    print("\nPDFs actualizados!")
