import re
from base64 import urlsafe_b64decode

from mcp.server.fastmcp import FastMCP

from gmail_mcp.client import get_service

mcp = FastMCP("private-gmail-mcp")


def _header(headers: list[dict], name: str) -> str:
    name = name.lower()
    for h in headers:
        if h.get("name", "").lower() == name:
            return h.get("value", "")
    return ""


def _label_index(service) -> tuple[dict[str, str], dict[str, dict]]:
    resp = service.users().labels().list(userId="me").execute()
    labels = resp.get("labels", [])
    name_to_id = {l["name"]: l["id"] for l in labels}
    by_id = {l["id"]: l for l in labels}
    return name_to_id, by_id


def _strip_html(html: str) -> str:
    text = re.sub(r"<style[^>]*>.*?</style>", "", html, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<script[^>]*>.*?</script>", "", text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _decode(data: str) -> str:
    return urlsafe_b64decode(data.encode("ascii")).decode("utf-8", errors="replace")


def _extract_body(payload: dict) -> str:
    if not payload:
        return ""

    mime = payload.get("mimeType", "")
    body = payload.get("body", {})

    if "data" in body:
        decoded = _decode(body["data"])
        if mime == "text/plain":
            return decoded
        if mime == "text/html":
            return _strip_html(decoded)

    plain: str | None = None
    html: str | None = None
    for part in payload.get("parts", []):
        m = part.get("mimeType", "")
        pb = part.get("body", {})
        if m == "text/plain" and "data" in pb and plain is None:
            plain = _decode(pb["data"])
        elif m == "text/html" and "data" in pb and html is None:
            html = _decode(pb["data"])
        elif m.startswith("multipart/"):
            inner = _extract_body(part)
            if inner and plain is None:
                plain = inner

    if plain:
        return plain
    if html:
        return _strip_html(html)
    return ""


@mcp.tool()
def list_unlabeled_emails(max_results: int = 50) -> list[dict]:
    """List the most recent emails that have no user-created labels.

    Uses the Gmail search query `has:nouserlabels`. Returns up to `max_results`
    items (default 50, capped at 100 by Gmail). Each entry contains id,
    thread_id, subject, sender, date, and snippet — usually enough to pick a
    label without fetching the full body.
    """
    service = get_service()
    max_results = max(1, min(max_results, 100))
    resp = (
        service.users()
        .messages()
        .list(userId="me", q="has:nouserlabels", maxResults=max_results)
        .execute()
    )

    out: list[dict] = []
    for m in resp.get("messages", []):
        msg = (
            service.users()
            .messages()
            .get(
                userId="me",
                id=m["id"],
                format="metadata",
                metadataHeaders=["Subject", "From", "Date"],
            )
            .execute()
        )
        headers = msg.get("payload", {}).get("headers", [])
        out.append(
            {
                "id": msg["id"],
                "thread_id": msg.get("threadId"),
                "subject": _header(headers, "Subject"),
                "from": _header(headers, "From"),
                "date": _header(headers, "Date"),
                "snippet": msg.get("snippet", ""),
            }
        )
    return out


@mcp.tool()
def get_email_content(email_id: str, max_chars: int = 10000) -> dict:
    """Fetch the full body of a specific email.

    Use this only when the subject/snippet from `list_unlabeled_emails` is not
    enough to decide on a label. The body is plain text (HTML is stripped) and
    truncated to `max_chars` characters to keep responses small.
    """
    service = get_service()
    msg = (
        service.users()
        .messages()
        .get(userId="me", id=email_id, format="full")
        .execute()
    )

    headers = msg.get("payload", {}).get("headers", [])
    body = _extract_body(msg.get("payload", {}))
    truncated = len(body) > max_chars
    if truncated:
        body = body[:max_chars]

    return {
        "id": msg["id"],
        "thread_id": msg.get("threadId"),
        "subject": _header(headers, "Subject"),
        "from": _header(headers, "From"),
        "to": _header(headers, "To"),
        "date": _header(headers, "Date"),
        "snippet": msg.get("snippet", ""),
        "body": body,
        "truncated": truncated,
    }


@mcp.tool()
def get_email_labels(email_id: str) -> list[dict]:
    """Return the labels currently applied to a specific email.

    Each item is `{id, name, type}` where type is "user" or "system".
    """
    service = get_service()
    msg = (
        service.users()
        .messages()
        .get(userId="me", id=email_id, format="minimal")
        .execute()
    )
    label_ids = msg.get("labelIds", [])
    _, by_id = _label_index(service)
    out: list[dict] = []
    for lid in label_ids:
        info = by_id.get(lid)
        if info:
            out.append(
                {"id": info["id"], "name": info["name"], "type": info.get("type", "user")}
            )
        else:
            out.append({"id": lid, "name": lid, "type": "unknown"})
    return out


@mcp.tool()
def list_labels(user_only: bool = True) -> list[dict]:
    """List all labels in the mailbox.

    Defaults to user-created labels only. Set `user_only=False` to also include
    Gmail's built-in system labels (INBOX, SPAM, CATEGORY_*, etc.).
    """
    service = get_service()
    resp = service.users().labels().list(userId="me").execute()
    labels = resp.get("labels", [])
    if user_only:
        labels = [l for l in labels if l.get("type") == "user"]
    return [
        {"id": l["id"], "name": l["name"], "type": l.get("type", "user")}
        for l in labels
    ]


@mcp.tool()
def add_label_to_email(email_id: str, label_name: str) -> dict:
    """Apply a label to an email by label name.

    The label must already exist — call `create_label` first if it does not.
    Returns the email id and its updated label name list.
    """
    service = get_service()
    name_to_id, by_id = _label_index(service)
    if label_name not in name_to_id:
        available = sorted(n for n, _ in name_to_id.items())
        raise RuntimeError(
            f"Label '{label_name}' does not exist. "
            f"Create it first with create_label. Existing labels: {available}"
        )
    label_id = name_to_id[label_name]

    msg = (
        service.users()
        .messages()
        .modify(userId="me", id=email_id, body={"addLabelIds": [label_id]})
        .execute()
    )
    return {
        "id": msg["id"],
        "labels": [by_id.get(lid, {}).get("name", lid) for lid in msg.get("labelIds", [])],
    }


@mcp.tool()
def create_label(name: str) -> dict:
    """Create a new user label. Idempotent — returns the existing label if the
    name is already taken.
    """
    service = get_service()
    name_to_id, _ = _label_index(service)
    if name in name_to_id:
        return {"id": name_to_id[name], "name": name, "created": False}

    label = (
        service.users()
        .labels()
        .create(
            userId="me",
            body={
                "name": name,
                "labelListVisibility": "labelShow",
                "messageListVisibility": "show",
            },
        )
        .execute()
    )
    return {"id": label["id"], "name": label["name"], "created": True}


def run() -> None:
    mcp.run()
