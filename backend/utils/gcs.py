from google.cloud import storage
import json
import os

# ---------------------------------------------------------
# Chargement credentials Render (JSON dans variable env)
# ---------------------------------------------------------
_credentials_json = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS_JSON")
if not _credentials_json:
    raise RuntimeError("Missing GOOGLE_APPLICATION_CREDENTIALS_JSON")

credentials_info = json.loads(_credentials_json)

storage_client = storage.Client.from_service_account_info(credentials_info)

# ---------------------------------------------------------
# Configuration bucket
# ---------------------------------------------------------
BUCKET_NAME = os.environ.get("GCS_BUCKET_NAME")
BASE_URL = os.environ.get("GCS_BASE_URL")   # ex: https://storage.googleapis.com/ratecard-media

if not BUCKET_NAME:
    raise RuntimeError("Missing GCS_BUCKET_NAME")

if not BASE_URL:
    raise RuntimeError("Missing GCS_BASE_URL")

bucket = storage_client.bucket(BUCKET_NAME)


# ==================================================================
# UPLOAD — compatible UBLA (ne touche JAMAIS aux ACL objet)
# ==================================================================
def upload_bytes(folder: str, filename: str, data: bytes: str = "image/jpeg") -> str:
    """
    Upload un fichier binaire dans GCS.
    Retourne l’URL publique (si bucket public).
    """

    path = f"{folder}/{filename}"
    blob = bucket.blob(path)

    blob.upload_from_string(
        data,
    )

    return f"{BASE_URL}/{path}"

def get_public_url(folder: str, filename: str | None) -> str | None:
    """
    Construit l’URL publique d’un fichier GCS à partir de son nom.
    Retourne None si filename est vide.
    """
    if not filename:
        return None
    return f"{BASE_URL}/{folder}/{filename}"



# ==================================================================
# DELETE — compatible UBLA
# ==================================================================
def delete_file(folder: str, filename: str):
    """
    Supprime un fichier dans GCS (ignore ACL).
    """
    path = f"{folder}/{filename}"
    blob = bucket.blob(path)

    try:
        blob.delete()   # Pas d’ACL, UBLA autorise la suppression via IAM
        return True
    except Exception:
        return False

