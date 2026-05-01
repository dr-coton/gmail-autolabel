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

## 사전 요구사항

- macOS / Linux
- Python 3.10+
- `uv` — `brew install uv`

---

## 설치 가이드 (상세)

### 1. Google Cloud 프로젝트 생성

1. https://console.cloud.google.com/ 접속 (본인 Gmail 계정으로 로그인)
2. 상단 좌측 **프로젝트 선택 드롭다운** 클릭 → **새 프로젝트**
3. 이름 아무거나 (예: `private-gmail-mcp`) → **만들기**
4. 생성 후 다시 드롭다운에서 그 프로젝트 **선택** ← 빼먹기 쉬움

### 2. Gmail API 활성화

1. 좌측 햄버거 메뉴 → **API 및 서비스 → 라이브러리**
2. 검색창에 `Gmail API` → 클릭 → **사용** 버튼
3. "사용 설정됨" 표시 뜨면 OK

### 3. OAuth 동의 화면 설정 ⚠️ 가장 헷갈리는 단계

1. 좌측 메뉴 → **API 및 서비스 → OAuth 동의 화면**
2. **User Type**:
   - 개인 `@gmail.com` 쓰면 무조건 **External** 선택
   - (Internal은 Google Workspace 조직 계정에서만 보임)
3. **만들기** → 양식 입력:
   - 앱 이름: `Private Gmail MCP` (아무거나)
   - 사용자 지원 이메일: 본인 이메일
   - 개발자 연락처: 본인 이메일
   - 나머지(앱 도메인, 로고)는 비워두면 됨
4. **저장 후 계속**
5. **범위(Scopes)** 단계: 그냥 **저장 후 계속** 누르고 넘어감
   - 여기서 추가 안 해도 됨. OAuth client가 요청 시 알아서 처리됨.
6. **테스트 사용자(Test users)** 단계:
   - **+ ADD USERS** → 본인 Gmail 주소 입력 → 추가
   - ⚠️ 이거 안 하면 인증 시 `403 access_denied` 떨어짐
7. **저장 후 계속** → 요약 화면 → 완료
8. **Publishing status: Testing** 상태로 남겨두기 (다음 섹션 참조)

### 4. OAuth 클라이언트 ID 발급

1. 좌측 메뉴 → **API 및 서비스 → 사용자 인증 정보(Credentials)**
2. 상단 **+ 사용자 인증 정보 만들기 → OAuth 클라이언트 ID**
3. **Application type: Desktop app** ← 중요. Web app 아님.
4. 이름 아무거나 (`gmail-mcp-desktop`)
5. **만들기** 누르면 client ID/secret 팝업
6. 팝업 우측 또는 목록에서 **JSON 다운로드** 버튼 클릭
7. 다운받은 파일 (`client_secret_xxxxx.json`) 을 다음 위치로 옮기고 이름 변경:

```bash
mkdir -p ~/.config/private-gmail-mcp
mv ~/Downloads/client_secret_*.json ~/.config/private-gmail-mcp/credentials.json
```

> 다른 경로에 두고 싶으면 `export GMAIL_MCP_CREDENTIALS=/path/to/credentials.json`

### 5. 7일 만료 함정 ⚠️ 반드시 알아두기

방금 동의 화면을 **Testing** 상태로 둔다고 했는데, Google 정책상:

> Testing 상태인 앱이 발급한 refresh token은 **7일 후 자동 만료**됨

→ 매주 한 번 재인증 필요 (브라우저 클릭 1번).

**해결책 3가지:**

| 옵션 | 장점 | 단점 |
|---|---|---|
| **A. Testing 유지 + 매주 재인증** | 즉시 사용 가능, 무료 | 매주 명령 1줄 실행 |
| **B. "Production" 게시** | refresh token 무한 | `gmail.modify`는 restricted scope라 Google 검수 필요 (수 주~수 개월, 개인용은 거의 통과 안 됨) |
| **C. Workspace + Internal 타입** | 검수 없이 무한 | Workspace(유료) 필요 |

**추천: A.** 만료되면 한 줄로 복구:
```bash
uvx --from git+https://github.com/dr-coton/private-gmail-mcp gmail-mcp auth --force
```

### 6. 최초 OAuth 인증

git URL에서 바로 실행. 브라우저가 열리며 Google 인증을 요청합니다.

```bash
uvx --from git+https://github.com/dr-coton/private-gmail-mcp gmail-mcp auth
```

진행 흐름:
1. 로컬에 임시 HTTP 서버 띄움 (랜덤 포트)
2. 기본 브라우저 자동으로 열림 → Google 로그인 화면
3. 본인 Gmail 계정 선택
4. **"Google에서 확인되지 않은 앱입니다" 경고** 등장 ← 정상
   - **고급(Advanced)** 클릭 → **`Private Gmail MCP`(안전하지 않음)으로 이동** 클릭
5. 권한 동의 화면 → **계속**
   - 실제 scope는 `gmail.modify` (메일 읽기 + 라벨 수정). 영구 삭제·전송 불가.
6. "인증 완료" 페이지로 자동 리다이렉트
7. 터미널에 `Authentication complete. Token saved to ...` 출력

토큰은 `~/.config/private-gmail-mcp/token.json` 에 저장됨.

### 7. Claude Desktop 등록

설정 파일 열기:
```bash
open -e ~/Library/Application\ Support/Claude/claude_desktop_config.json
```

(파일 없으면 새로 만들기). 다음 추가:

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

이미 다른 설정(`preferences` 등)이 있으면 그 객체 안에 `mcpServers` 키만 추가.
JSON 콤마/괄호 빠뜨리지 말 것.

저장 후 **Claude Desktop 완전 종료(⌘Q) 후 재실행**.

### 8. 동작 확인

Claude Desktop에서 새 대화 시작 → 우측 하단 도구 아이콘 → `private-gmail` 서버
및 툴 6개 보이면 성공.

테스트 한마디:
> 내 Gmail 라벨 목록 보여줘

`list_labels` 호출 결과가 떠야 정상.

---

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

---

## 토큰 갱신 / 재인증

7일 만료 또는 토큰 손상 시 한 줄로 처리:

```bash
uvx --from git+https://github.com/dr-coton/private-gmail-mcp gmail-mcp auth --force
```

`--force`(또는 동등한 `--refresh`)가 하는 일:
- 기존 `token.json` 삭제
- Google에 `prompt=consent` 보내서 새 refresh token 강제 발급

플래그 없이 그냥 `auth` 만 돌려도 되지만, 이전 동의가 캐시돼서 새 refresh token이
안 떨어질 수 있음 → 만료 복구는 `--force` 권장.

---

## 패키지 업데이트

`uvx`는 git URL을 캐시합니다. 새 버전을 받으려면:
```bash
uvx --refresh --from git+https://github.com/dr-coton/private-gmail-mcp gmail-mcp --help
```

`auth` 와 함께 쓸 때:
```bash
# uvx 캐시 갱신 + OAuth 재인증
uvx --refresh --from git+https://github.com/dr-coton/private-gmail-mcp gmail-mcp auth --force
```

---

## 권한 범위

`https://www.googleapis.com/auth/gmail.modify` — 메일 읽기 + 라벨 수정.
삭제/전송 권한은 요청하지 않습니다.

토큰 무효화하려면 https://myaccount.google.com/permissions 에서 앱 제거.

---

## 자주 만나는 에러

| 에러 | 원인 / 해결 |
|---|---|
| `403 access_denied` (브라우저) | 동의 화면 Test users에 본인 이메일 추가 안 됨 → 3-6단계 |
| `redirect_uri_mismatch` | OAuth client를 "Web app"으로 만듦 → 삭제하고 "Desktop app"으로 재발급 |
| `invalid_grant: Token has been expired or revoked` | 7일 만료 → `gmail-mcp auth --force` |
| `Token not found` (MCP 시작 시) | `auth` 명령 안 돌렸거나 경로 다름 → 6단계 다시 |
| Claude에서 툴 안 보임 | config JSON 문법 오류 (콤마/괄호) 또는 Claude Desktop 재시작 안 함 |
| `uvx: command not found` | `brew install uv` |
| Claude Desktop 로그 보고 싶을 때 | `~/Library/Logs/Claude/mcp*.log` |

---

## 로컬 개발 (선택)

코드를 직접 수정하면서 테스트할 때만 필요:
```bash
git clone https://github.com/dr-coton/private-gmail-mcp
cd private-gmail-mcp
uv sync
uv run gmail-mcp auth
```

Claude Desktop config:
```json
{
  "mcpServers": {
    "private-gmail": {
      "command": "uv",
      "args": [
        "--directory",
        "/path/to/private-gmail-mcp",
        "run",
        "gmail-mcp"
      ]
    }
  }
}
```
