
from io import BytesIO
from pypdf import PdfReader


def extract_resume_text(pdf_bytes: bytes):
    """
    Extract text from an uploaded PDF resume.
    """

    try:
        pdf_file = BytesIO(pdf_bytes)
        reader = PdfReader(pdf_file)

        if reader.is_encrypted:
            raise ValueError(
                "Password-protected PDFs are not supported."
            )

        extracted_pages = []

        for page_number, page in enumerate(reader.pages, start=1):
            page_text = page.extract_text() or ""

            if page_text.strip():
                extracted_pages.append(page_text.strip())

        full_text = "\n\n".join(extracted_pages).strip()

        if not full_text:
            raise ValueError(
                "No readable text found. The PDF may contain scanned images."
            )

        return {
            "extracted_text": full_text,
            "page_count": len(reader.pages),
            "character_count": len(full_text)
        }

    except ValueError:
        raise

    except Exception as error:
        print("PDF EXTRACTION ERROR:", error)
        raise ValueError(
            "Unable to read this PDF. Please upload a valid PDF resume."
        )
