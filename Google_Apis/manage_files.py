from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

SCOPES = ["https://www.googleapis.com/auth/drive"]

creds = service_account.Credentials.from_service_account_file(
    "credentials.json",
    scopes=SCOPES
)

drive_service = build(
    "drive",
    "v3",
    credentials=creds
)

file_metadata = {
    "name": "meeting.txt",
    "parents": ["1Ql44PDmjPRKUxjHAT_znV_E-OChvEVdz"]
}

media = MediaFileUpload(
    "meeting.txt",
    mimetype="text/plain"
)

file = drive_service.files().create(
    body=file_metadata,
    media_body=media,
    fields="id,name"
).execute()

print("Uploaded Successfully")
print("File ID:", file["id"])
print("File Name:", file["name"])