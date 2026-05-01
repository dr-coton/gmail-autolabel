<div align="center">

# Gmail Autolabel

**AI-powered automatic Gmail labeling for Claude Desktop.**
Stop manually triaging your inbox — let Claude read, classify, and file your mail.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![MCP](https://img.shields.io/badge/MCP-server-8A2BE2.svg)](https://modelcontextprotocol.io/)
[![Claude Desktop](https://img.shields.io/badge/Claude-Desktop-D97757.svg)](https://claude.ai/download)

**English** · [한국어](./README.ko.md) · [中文](./README.zh.md) · [日本語](./README.ja.md)

<br>

<img src="./docs/hero.png" alt="Gmail inbox after triage by gmail-autolabel — every message classified with a colored label" width="900">

<sub><i>An inbox after Claude has triaged it: receipts, security alerts, newsletters, travel, work — every message classified, with multilingual support out of the box.</i></sub>

</div>

---

## What it does

`gmail-autolabel` is a [Model Context Protocol](https://modelcontextprotocol.io/)
server that lets Claude Desktop classify and label your Gmail automatically.

Point Claude at your inbox, and it will:

1. Pull the most recent emails that have **no user labels** (`has:nouserlabels`)
2. Read the subject and sender — fetch the body only when ambiguous
3. Apply an existing label, or create a new one if needed
4. Fall back to a **"Needs Review"** label when genuinely uncertain

You stay in control: every label decision is made by Claude using your prompt,
not by hard-coded rules. Run it on demand or schedule it.

## Quick demo

In Claude Desktop, simply say:

> Triage my unlabeled inbox. For unclear ones, read the body. If you can't
> decide, label them "Needs Review".

Claude will run something like:

```
list_labels()                        # see existing categories
list_unlabeled_emails(50)            # 50 emails to triage
get_email_content(<id>)              # only for ambiguous ones
add_label_to_email(<id>, "Receipts") # apply a label
create_label("Newsletters")          # or create a new one
```

## Why this vs. the official Gmail MCP

|                  | Official Gmail MCP (claude.ai) | gmail-autolabel              |
| ---------------- | ------------------------------ | ---------------------------- |
| Hosting          | Anthropic-hosted               | **Local on your machine**    |
| OAuth scope      | Full read / send / modify      | `gmail.modify` only          |
| Send / delete    | Allowed                        | **Not allowed**              |
| Data flow        | Through Anthropic              | Direct: your laptop ↔ Google |
| Customization    | Fixed tool set                 | You own the code             |
| Focus            | General Gmail use              | Optimized for label triage   |

If you want a focused, transparent, locally-run tool for inbox triage with
minimal scopes, this is for you.

## Tools

| Tool                                          | Description                                            |
| --------------------------------------------- | ------------------------------------------------------ |
| `list_unlabeled_emails(max_results=50)`       | Recent emails with no user labels (`has:nouserlabels`) |
| `get_email_content(email_id, max_chars=10000)` | Full body — HTML stripped, length-capped              |
| `get_email_labels(email_id)`                  | Labels on a specific email                             |
| `list_labels(user_only=True)`                 | All labels in the mailbox                              |
| `add_label_to_email(email_id, label_name)`    | Apply a label by name (must already exist)             |
| `create_label(name)`                          | Create a label (idempotent)                            |

## Prerequisites

- macOS or Linux
- Python 3.10+
- [`uv`](https://github.com/astral-sh/uv) — `brew install uv`

---

## Installation

### 1. Create a Google Cloud project

1. Go to <https://console.cloud.google.com/> and sign in with your Gmail account.
2. Click the project dropdown at the top → **New Project**.
3. Name it anything (e.g. `gmail-autolabel`) → **Create**.
4. Make sure that project is selected after creation.

### 2. Enable the Gmail API

1. Sidebar → **APIs & Services → Library**.
2. Search `Gmail API` → click → **Enable**.

### 3. Configure the OAuth consent screen ⚠️ easy to misstep

1. Sidebar → **APIs & Services → OAuth consent screen**.
2. **User Type**: choose **External** (Internal is for Workspace orgs only).
3. Fill in app name (e.g. `Gmail Autolabel`), your email for support, your
   email for developer contact. Leave the optional fields blank.
4. **Save and Continue**.
5. **Scopes**: just **Save and Continue** — the OAuth client will request the
   scope at runtime, you don't need to add it here.
6. **Test users**: click **+ ADD USERS** and add **your own Gmail address**.
   ⚠️ Skipping this causes `403 access_denied` at sign-in.
7. **Save and Continue** → finish. Leave the app in **Testing** status (see §5).

### 4. Create a Desktop OAuth client

1. Sidebar → **APIs & Services → Credentials**.
2. **+ CREATE CREDENTIALS → OAuth client ID**.
3. **Application type: Desktop app** ← important. Not Web app.
4. Name it `gmail-autolabel-desktop` (or anything).
5. Click **Create**, then download the JSON.
6. Move and rename the file:

   ```bash
   mkdir -p ~/.config/gmail-autolabel
   mv ~/Downloads/client_secret_*.json ~/.config/gmail-autolabel/credentials.json
   ```

   To use a different path, set `GMAIL_AUTOLABEL_CREDENTIALS=/path/to/credentials.json`.

### 5. ⚠️ The 7-day expiration trap

Apps in **Testing** status issue refresh tokens that **expire after 7 days**.
This is a Google policy, not a bug.

Three ways to handle it:

| Option                                | Pros                       | Cons                                                                |
| ------------------------------------- | -------------------------- | ------------------------------------------------------------------- |
| **A. Stay in Testing, re-auth weekly** | Free, instant              | One command per week                                                |
| **B. Publish to Production**          | Tokens never expire        | `gmail.modify` is a restricted scope → Google verification required |
| **C. Workspace + Internal type**      | No verification, unlimited | Requires paid Google Workspace                                      |

**Recommended: A.** When tokens expire, recover with one command (see §Re-authentication).

### 6. First-time OAuth

```bash
uvx --from git+https://github.com/dr-coton/gmail-autolabel gmail-autolabel auth
```

What happens:

1. A local HTTP server starts on a random port.
2. Your browser opens to Google's sign-in page.
3. Pick your Gmail account.
4. **"Google hasn't verified this app"** warning appears — this is expected.
   Click **Advanced** → **Go to Gmail Autolabel (unsafe)**.
5. Grant permissions → page redirects back to localhost.
6. Terminal prints `Authentication complete. Token saved to ...`.

The token is stored at `~/.config/gmail-autolabel/token.json`.

### 7. Configure Claude Desktop

Open the config file:

```bash
open -e ~/Library/Application\ Support/Claude/claude_desktop_config.json
```

Add the `mcpServers` entry (merge with any existing config):

```json
{
  "mcpServers": {
    "gmail-autolabel": {
      "command": "uvx",
      "args": [
        "--from",
        "git+https://github.com/dr-coton/gmail-autolabel",
        "gmail-autolabel"
      ]
    }
  }
}
```

Save → **fully quit Claude Desktop (⌘Q) and relaunch**.

### 8. Verify

Open a new chat in Claude Desktop, click the tools icon, and you should see
`gmail-autolabel` with 6 tools listed. Try:

> Show me my Gmail labels.

If `list_labels` returns a list, you're done.

---

## Re-authentication

When tokens expire (every 7 days in Testing mode), recover with one command:

```bash
uvx --from git+https://github.com/dr-coton/gmail-autolabel gmail-autolabel auth --force
```

What `--force` (alias `--refresh`) does:

- Deletes the existing `token.json`
- Sends `prompt=consent` to Google so a fresh refresh token is issued

Without `--force`, Google may cache your previous consent and return only an
access token — leading to the same expiration a week later. Use `--force` for
recovery.

## Updating

`uvx` caches the git URL. To pull a new version:

```bash
uvx --refresh --from git+https://github.com/dr-coton/gmail-autolabel gmail-autolabel --help
```

Combined cache refresh + re-auth:

```bash
uvx --refresh --from git+https://github.com/dr-coton/gmail-autolabel gmail-autolabel auth --force
```

## Permissions

This server requests **only** the `https://www.googleapis.com/auth/gmail.modify`
scope: read messages and modify labels. It **cannot** send mail, delete mail,
or change account settings.

To revoke at any time: <https://myaccount.google.com/permissions>.

## Troubleshooting

| Error                                            | Cause / Fix                                                                          |
| ------------------------------------------------ | ------------------------------------------------------------------------------------ |
| `403 access_denied` (in browser)                 | Your email isn't in Test users. See §3 step 6.                                       |
| `redirect_uri_mismatch`                          | OAuth client was created as "Web app". Recreate as **Desktop app**.                  |
| `invalid_grant: Token has been expired or revoked` | 7-day expiration. Run `gmail-autolabel auth --force`.                              |
| `Token not found` (when MCP starts)              | Auth not completed. Re-run §6.                                                       |
| Tools don't show up in Claude Desktop            | JSON syntax error in config, or app wasn't fully relaunched.                         |
| `uvx: command not found`                         | `brew install uv`                                                                    |
| Inspect Claude Desktop MCP logs                  | `~/Library/Logs/Claude/mcp*.log`                                                     |

## Local development

```bash
git clone https://github.com/dr-coton/gmail-autolabel
cd gmail-autolabel
uv sync
uv run gmail-autolabel auth
```

Claude Desktop config for the local checkout:

```json
{
  "mcpServers": {
    "gmail-autolabel": {
      "command": "uv",
      "args": [
        "--directory",
        "/path/to/gmail-autolabel",
        "run",
        "gmail-autolabel"
      ]
    }
  }
}
```

## Roadmap

- [ ] Batch labeling beyond 50 emails per run
- [ ] Customizable label suggestion prompts shipped as a system prompt
- [ ] Headless re-auth (cron-friendly)
- [ ] Smart unsubscribe / archive suggestions
- [ ] Support for additional MCP clients (Cursor, etc.)

## Contributing

PRs welcome. For non-trivial changes, please open an issue first to discuss.

## License

[MIT](LICENSE) © 2026 dr-coton
