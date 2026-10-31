"""Step 5: upload to YouTube (Data API v3). One-time OAuth login opens a browser."""
import os
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]


def _service():
    if os.getenv("YT_REFRESH_TOKEN"):  # headless (GitHub Actions)
        creds = Credentials(None, refresh_token=os.environ["YT_REFRESH_TOKEN"],
                            token_uri="https://oauth2.googleapis.com/token",
                            client_id=os.environ["YT_CLIENT_ID"],
                            client_secret=os.environ["YT_CLIENT_SECRET"], scopes=SCOPES)
        creds.refresh(Request())
        return build("youtube", "v3", credentials=creds)
    creds = None
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("client_secret.json", SCOPES)
            creds = flow.run_local_server(port=0)
        open("token.json", "w").write(creds.to_json())
    return build("youtube", "v3", credentials=creds)


def upload(path, title, description, tags, privacy="private", publish_at=None):
    """privacy: private | unlisted | public. publish_at: RFC3339 UTC e.g. 2026-11-02T12:00:00Z (needs private)."""
    status = {"privacyStatus": privacy, "selfDeclaredMadeForKids": False,
              "containsSyntheticMedia": True}  # YouTube requires disclosing AI-generated content
    if publish_at:
        status.update(privacyStatus="private", publishAt=publish_at)
    body = {"snippet": {"title": title[:100], "description": description, "tags": tags,
                        "categoryId": "28"},  # Science & Technology
            "status": status}
    req = _service().videos().insert(part="snippet,status", body=body,
                                     media_body=MediaFileUpload(path, chunksize=-1, resumable=True))
    resp = None
    while resp is None:
        _, resp = req.next_chunk()
    return f"https://youtu.be/{resp['id']}"
