from pydantic import BaseModel


# ============================================================
# EMAIL DOCUMENT
# ============================================================

class EmailDocument(BaseModel):

    subject: str

    html: str

    text: str = ""
