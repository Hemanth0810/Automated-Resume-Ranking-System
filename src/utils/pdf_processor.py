import io
import base64
from PIL import Image
from poppler import PopplerDocument # Import PopplerDocument

def input_pdf_setup(uploaded_file):
    if uploaded_file is not None:
        # Read the PDF content directly
        pdf_bytes = uploaded_file.read()

        # Create a PopplerDocument from bytes
        # Use PopplerDocument directly instead of pdf2image
        doc = PopplerDocument.from_bytes(pdf_bytes)

        # Render the first page
        # PopplerDocument.create_image takes page number (0-indexed) and scale
        # Default scale often produces good enough resolution
        first_page_image_data = doc.create_image(0)

        # Convert to PIL Image
        # python-poppler returns image data, often in a format suitable for PIL
        first_page = Image.frombytes(
            first_page_image_data.mode,
            (first_page_image_data.width, first_page_image_data.height),
            first_page_image_data.data
        )

        # Convert to bytes (JPEG)
        img_byte_arr = io.BytesIO()
        first_page.save(img_byte_arr, format="JPEG")
        img_byte_arr = img_byte_arr.getvalue()

        pdf_parts = [
            {
                "mime_type": "image/jpeg",
                "data": base64.b64encode(img_byte_arr).decode()
            }
        ]
        return pdf_parts
    else:
        raise FileNotFoundError("No file uploaded")