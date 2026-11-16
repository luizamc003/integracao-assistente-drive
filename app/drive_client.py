import io

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

from app.config import GOOGLE_DRIVE_FOLDER_ID, GOOGLE_SERVICE_ACCOUNT_FILE

SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]


def get_drive_service():
    credentials = service_account.Credentials.from_service_account_file(
        GOOGLE_SERVICE_ACCOUNT_FILE, scopes=SCOPES
    )
    return build("drive", "v3", credentials=credentials)


def list_pdfs(folder_id: str = GOOGLE_DRIVE_FOLDER_ID):
    service = get_drive_service()
    query = f"'{folder_id}' in parents and mimeType='application/pdf' and trashed=false"
    results = service.files().list(
        q=query,
        fields="files(id, name, modifiedTime, md5Checksum)",
    ).execute()
    return results.get("files", [])


def download_file(file_id: str) -> bytes:
    service = get_drive_service()
    request = service.files().get_media(fileId=file_id)
    buffer = io.BytesIO()
    downloader = MediaIoBaseDownload(buffer, request)
    done = False
    while not done:
        _, done = downloader.next_chunk()
    return buffer.getvalue()
