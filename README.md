# private-gmail-mcp

Claude Desktop에서 사용할 커스텀 Gmail MCP 서버. 라벨이 지정되지 않은 메일을
일괄 분류하기 위한 6개의 툴을 제공합니다.

## 제공 툴

| 툴 | 설명 |
| --- | --- |
| `list_unlabeled_emails(max_results=50)` | 사용자 라벨이 없는 최신순 메일 N개 (`has:nouserlabels`) |
| `get_email_content(email_id, max_chars=10000)` | 특정 메일의 본문 (HTML은 텍스트로 변환) |
| `get_email_labels(email_id)` | 메일에 붙어있는 라벨 목록 |
| `list_labels(user_only=True)` | 메일함 전체 라벨 목록 |
| `add_label_to_email(email_id, label_name)` | 메일에 라벨 적용 (이름 기준, 존재해야 함) |
| `create_label(name)` | 새 라벨 생성 (멱등) |

## 설치

`uv` 필요 (없으면 `brew install uv`).

### 1) Google Cloud OAuth 클라이언트 발급

1. [Google Cloud Console](https://console.cloud.google.com/) → 프로젝트 생성
2. **APIs & Services → Library** → "Gmail API" 활성화
3. **APIs & Services → OAuth consent screen** → External, 본인 이메일을 테스트 사용자로 추가
4. **APIs & Services → Credentials** → **Create Credentials → OAuth client ID**
   - Application type: **Desktop app**
5. 다운받은 JSON을 아래 위치에 저장:
   ```
   ~/.config/private-gmail-mcp/credentials.json
   ```
   다른 경로에 두려면 `GMAIL_MCP_CREDENTIALS` 환경변수로 지정.

### 2) 최초 OAuth 인증 (한 번만)

git URL에서 바로 실행. 브라우저가 열리며 Google 인증을 요청합니다.
토큰은 `~/.config/private-gmail-mcp/token.json` 에 저장됩니다.

```bash
uvx --from git+https://github.com/dr-coton/private-gmail-mcp gmail-mcp auth
```

### 3) Claude Desktop 설정

`~/Library/Application Support/Claude/claude_desktop_config.json` 에 추가:

```json
{
  "mcpServers": {
    "private-gmail": {
      "command": "uvx",
      "args": [
        "--from",
        "git+https://github.com/dr-coton/private-gmail-mcp",
        "gmail-mcp"
      ]
    }
  }
}
```

설정 저장 후 Claude Desktop을 재시작.

### 업데이트

`uvx`는 git URL을 캐시합니다. 새 버전을 받으려면:
```bash
uvx --refresh --from git+https://github.com/dr-coton/private-gmail-mcp gmail-mcp --help
```

### 로컬 개발 (선택)

코드를 직접 수정하면서 테스트할 때만 필요:
```bash
git clone https://github.com/dr-coton/private-gmail-mcp
cd private-gmail-mcp
uv sync
uv run gmail-mcp auth
```
이 경우 Claude Desktop config는 `command: "uv"`, `args: ["--directory", "<로컬경로>", "run", "gmail-mcp"]` 형태로.

## 사용 시나리오

Claude에게 다음과 같이 지시:

> 라벨이 지정되지 않은 최신 메일 50개를 가져와서 각각 적절한 라벨을 지정해줘.
> subject/snippet으로 충분히 판단되면 그걸로 분류하고, 애매한 메일은
> `get_email_content`로 본문을 읽고 분류해. 그래도 도저히 판단이 어려우면
> `메일 검토 필요` 라벨을 (없으면 생성해서) 붙여줘.

Claude가 실행하는 흐름:
1. `list_labels()` — 어떤 라벨들이 이미 있는지 확인
2. `list_unlabeled_emails(50)` — 분류 대상 50건
3. 메일별로 판단 → 필요하면 `get_email_content` → 필요하면 `create_label` → `add_label_to_email`

## 권한 범위

`https://www.googleapis.com/auth/gmail.modify` — 메일 읽기 + 라벨 수정.
삭제/전송 권한은 요청하지 않습니다.

## 토큰 갱신

OAuth consent screen이 **Testing** 상태인 경우 refresh token이 7일 후 만료됩니다.
다음 한 줄로 토큰 삭제 + 강제 재인증을 한 번에 처리:

```bash
uvx --from git+https://github.com/dr-coton/private-gmail-mcp gmail-mcp auth --force
```

`--force`(또는 동등한 `--refresh`)가 하는 일:
- 기존 `token.json` 삭제
- Google에 `prompt=consent` 보내서 새 refresh token 강제 발급

플래그 없이 그냥 `auth` 만 돌려도 인증은 되지만, 이전 동의가 캐시돼서 새 refresh token이
안 떨어질 수 있어 만료 복구 시에는 `--force` 사용을 권장합니다.

## 문제 해결

- **"Token not found"** → `gmail-mcp auth` 를 먼저 실행했는지 확인
- **OAuth 동의 화면에서 "앱이 확인되지 않음"** → 정상. "고급 → 안전하지 않은 페이지로 이동" 클릭
- **`invalid_grant` / 토큰 만료** → `gmail-mcp auth --force` 실행
- **다른 경로에 credentials 두기** → `export GMAIL_MCP_CREDENTIALS=/path/to/credentials.json`
