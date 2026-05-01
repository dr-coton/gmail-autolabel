import os
import sys
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/gmail.modify"]


def _config_dir() -> Path:
    base = os.environ.get("GMAIL_MCP_CONFIG_DIR")
    if base:
        return Path(base).expanduser()
    return Path.home() / ".config" / "private-gmail-mcp"


def _credentials_path() -> Path:
    if p := os.environ.get("GMAIL_MCP_CREDENTIALS"):
        return Path(p).expanduser()
    return _config_dir() / "credentials.json"


def _token_path() -> Path:
    return _config_dir() / "token.json"


def run_oauth_flow() -> None:
    creds_path = _credentials_path()
    if not creds_path.exists():
        print(f"ERROR: credentials.json not found at {creds_path}", file=sys.stderr)
        print(
            "Download an OAuth client (Desktop app) from Google Cloud Console "
            "and place it at the path above, or set GMAIL_MCP_CREDENTIALS.",
            file=sys.stderr,
        )
        sys.exit(1)

    config = _config_dir()
    config.mkdir(parents=True, exist_ok=True)

    flow = InstalledAppFlow.from_client_secrets_file(str(creds_path), SCOPES)
    creds = flow.run_local_server(port=0)
    _token_path().write_text(creds.to_json())
    print(f"Authentication complete. Token saved to {_token_path()}")


def get_service():
    token_path = _token_path()
    if not token_path.exists():
        raise RuntimeError(
            f"Token not found at {token_path}. "
            "Run `python -m gmail_mcp auth` (or `gmail-mcp auth`) first."
        )
    creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)
    if not creds.valid:
        if creds.expired and creds.refresh_token:
            creds.refresh(Request())
            token_path.write_text(creds.to_json())
        else:
            raise RuntimeError(
                "Stored credentials are invalid. Re-run `python -m gmail_mcp auth`."
            )
    return build("gmail", "v1", credentials=creds, cache_discovery=False)
