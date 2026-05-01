<div align="center">

# Gmail Autolabel

**Claude Desktop을 위한 AI 기반 Gmail 자동 라벨링.**
받은편지함을 일일이 정리하지 마세요. Claude가 읽고, 분류하고, 라벨까지 붙여줍니다.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![MCP](https://img.shields.io/badge/MCP-server-8A2BE2.svg)](https://modelcontextprotocol.io/)
[![Claude Desktop](https://img.shields.io/badge/Claude-Desktop-D97757.svg)](https://claude.ai/download)

[English](./README.md) · **한국어** · [中文](./README.zh.md) · [日本語](./README.ja.md)

</div>

---

## 어떤 도구인가요

`gmail-autolabel`은 [Model Context Protocol](https://modelcontextprotocol.io/)
서버로, Claude Desktop이 여러분의 Gmail을 자동으로 분류하고 라벨링할 수 있게 해줍니다.

Claude를 받은편지함에 연결하면:

1. **사용자 라벨이 없는** 최신 메일을 가져옵니다 (`has:nouserlabels`)
2. 제목과 발신자를 먼저 보고, 애매할 때만 본문을 읽습니다
3. 적절한 기존 라벨을 적용하거나, 필요하면 새 라벨을 만듭니다
4. 도저히 판단이 안 서면 **"메일 검토 필요"** 라벨로 보류합니다

규칙은 하드코딩되어 있지 않습니다. 모든 분류 판단은 여러분의 프롬프트를 보고
Claude가 직접 수행합니다. 필요할 때 실행하거나 스케줄링할 수 있습니다.

## 빠른 데모

Claude Desktop에서 이렇게 말해보세요:

> 라벨이 없는 메일들 분류해줘. 애매하면 본문 읽고 판단하고, 그래도 모르겠으면
> "메일 검토 필요" 라벨 붙여줘.

Claude는 다음과 같이 실행합니다:

```
list_labels()                          # 기존 라벨 확인
list_unlabeled_emails(50)              # 분류할 50건
get_email_content(<id>)                # 애매한 메일 본문
add_label_to_email(<id>, "영수증")     # 라벨 적용
create_label("뉴스레터")                # 또는 새 라벨 생성
```

## 공식 Gmail MCP와의 차이

|              | 공식 Gmail MCP (claude.ai)   | gmail-autolabel              |
| ------------ | ---------------------------- | ---------------------------- |
| 호스팅       | Anthropic 서버               | **로컬 머신**                |
| OAuth 권한   | 읽기/전송/수정 전체          | `gmail.modify` 만            |
| 전송/삭제    | 가능                         | **불가능**                   |
| 데이터 흐름  | Anthropic 경유               | 본인 노트북 ↔ Google 직접 |
| 커스터마이징 | 고정된 툴셋                  | 코드 직접 소유               |
| 초점         | 일반 Gmail 사용              | 라벨 분류 워크플로 특화      |

받은편지함 정리에 특화된, 투명하고 로컬에서 실행되며 최소 권한만 사용하는
도구를 원하신다면 이 프로젝트가 맞습니다.

## 제공 툴

| 툴                                            | 설명                                              |
| --------------------------------------------- | ------------------------------------------------- |
| `list_unlabeled_emails(max_results=50)`       | 사용자 라벨이 없는 최신순 메일 (`has:nouserlabels`) |
| `get_email_content(email_id, max_chars=10000)` | 본문 전체 (HTML 변환, 길이 제한)                |
| `get_email_labels(email_id)`                  | 특정 메일에 붙은 라벨                             |
| `list_labels(user_only=True)`                 | 메일함 전체 라벨 목록                             |
| `add_label_to_email(email_id, label_name)`    | 라벨 이름으로 적용 (사전 존재 필수)               |
| `create_label(name)`                          | 라벨 생성 (멱등)                                  |

## 사전 요구사항

- macOS 또는 Linux
- Python 3.10+
- [`uv`](https://github.com/astral-sh/uv) — `brew install uv`

---

## 설치 가이드

### 1. Google Cloud 프로젝트 생성

1. <https://console.cloud.google.com/> 접속, Gmail 계정으로 로그인
2. 상단 프로젝트 드롭다운 → **새 프로젝트**
3. 이름 아무거나 (`gmail-autolabel` 등) → **만들기**
4. 생성 후 그 프로젝트가 선택됐는지 확인

### 2. Gmail API 활성화

1. 좌측 메뉴 → **API 및 서비스 → 라이브러리**
2. `Gmail API` 검색 → 클릭 → **사용**

### 3. OAuth 동의 화면 설정 ⚠️ 가장 헷갈림

1. 좌측 메뉴 → **API 및 서비스 → OAuth 동의 화면**
2. **User Type**: **External** 선택 (Internal은 Workspace 전용)
3. 앱 이름 (`Gmail Autolabel`), 지원 이메일, 개발자 이메일 입력. 나머지는 비워둠
4. **저장 후 계속**
5. **범위(Scopes)**: 그대로 **저장 후 계속** — OAuth client가 런타임에 요청
6. **테스트 사용자(Test users)**: **+ ADD USERS** → 본인 Gmail 추가
   ⚠️ 이거 빼먹으면 인증 시 `403 access_denied`
7. **저장 후 계속** → 완료. **Testing** 상태 유지 (§5 참조)

### 4. Desktop OAuth 클라이언트 발급

1. 좌측 메뉴 → **API 및 서비스 → 사용자 인증 정보**
2. **+ 사용자 인증 정보 만들기 → OAuth 클라이언트 ID**
3. **Application type: Desktop app** ← 중요. Web app 아님
4. 이름 `gmail-autolabel-desktop` (아무거나)
5. **만들기** → JSON 다운로드
6. 파일 이동 및 이름 변경:

   ```bash
   mkdir -p ~/.config/gmail-autolabel
   mv ~/Downloads/client_secret_*.json ~/.config/gmail-autolabel/credentials.json
   ```

   다른 경로 사용 시 `GMAIL_AUTOLABEL_CREDENTIALS=/path/to/credentials.json` 설정

### 5. ⚠️ 7일 만료 함정

**Testing** 상태 앱이 발급한 refresh token은 **7일 후 만료**됩니다. Google 정책입니다.

| 옵션                              | 장점               | 단점                                                |
| --------------------------------- | ------------------ | --------------------------------------------------- |
| **A. Testing 유지 + 매주 재인증** | 무료, 즉시 사용    | 매주 명령 1줄                                       |
| **B. Production 게시**            | 토큰 무한          | `gmail.modify`는 restricted scope → Google 검수 필요 |
| **C. Workspace + Internal**       | 검수 없이 무한     | 유료 Workspace 필요                                 |

**추천: A.** 만료 시 한 줄로 복구 (§재인증 참조).

### 6. 최초 OAuth 인증

```bash
uvx --from git+https://github.com/dr-coton/gmail-autolabel gmail-autolabel auth
```

진행 흐름:

1. 로컬 HTTP 서버 시작 (랜덤 포트)
2. 브라우저 자동 열림 → Google 로그인
3. 본인 Gmail 계정 선택
4. **"확인되지 않은 앱입니다"** 경고 표시 — 정상.
   **고급** → **Gmail Autolabel(안전하지 않음)으로 이동** 클릭
5. 권한 허용 → localhost로 리다이렉트
6. 터미널에 `Authentication complete. Token saved to ...` 출력

토큰 저장 위치: `~/.config/gmail-autolabel/token.json`

### 7. Claude Desktop 설정

```bash
open -e ~/Library/Application\ Support/Claude/claude_desktop_config.json
```

`mcpServers` 추가 (기존 설정과 병합):

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

저장 → **Claude Desktop 완전 종료(⌘Q) 후 재실행**

### 8. 동작 확인

Claude Desktop에서 새 대화, 우측 하단 도구 아이콘 → `gmail-autolabel` 6개 툴 확인:

> 내 Gmail 라벨 보여줘

`list_labels` 결과가 뜨면 성공.

---

## 재인증

토큰 만료(Testing 모드 7일) 시 한 줄 복구:

```bash
uvx --from git+https://github.com/dr-coton/gmail-autolabel gmail-autolabel auth --force
```

`--force`(또는 `--refresh`)가 하는 일:

- 기존 `token.json` 삭제
- Google에 `prompt=consent` 전송 → 새 refresh token 발급

플래그 없이 그냥 `auth`만 돌리면 Google이 이전 동의를 캐시하고 access token만
줄 수 있어 1주일 뒤 같은 문제 반복. 복구 시에는 `--force` 권장.

## 업데이트

`uvx`는 git URL을 캐시합니다. 새 버전 받기:

```bash
uvx --refresh --from git+https://github.com/dr-coton/gmail-autolabel gmail-autolabel --help
```

캐시 갱신 + 재인증 함께:

```bash
uvx --refresh --from git+https://github.com/dr-coton/gmail-autolabel gmail-autolabel auth --force
```

## 권한

`https://www.googleapis.com/auth/gmail.modify` 만 요청 — 메일 읽기 + 라벨 수정.
메일 전송/삭제/계정 설정 변경은 **불가능**.

언제든 권한 취소: <https://myaccount.google.com/permissions>

## 자주 만나는 에러

| 에러                                              | 원인 / 해결                                                          |
| ------------------------------------------------- | -------------------------------------------------------------------- |
| `403 access_denied` (브라우저)                    | Test users에 본인 이메일 미추가 → §3 6단계                           |
| `redirect_uri_mismatch`                           | OAuth client를 "Web app"으로 만듦 → **Desktop app**으로 재발급       |
| `invalid_grant: Token has been expired or revoked` | 7일 만료 → `gmail-autolabel auth --force`                          |
| `Token not found` (MCP 시작 시)                   | 인증 미완료 → §6 재실행                                              |
| Claude Desktop에 툴 안 보임                       | config JSON 문법 오류, 또는 완전 종료 안 함                          |
| `uvx: command not found`                          | `brew install uv`                                                    |
| MCP 로그 보기                                     | `~/Library/Logs/Claude/mcp*.log`                                     |

## 로컬 개발

```bash
git clone https://github.com/dr-coton/gmail-autolabel
cd gmail-autolabel
uv sync
uv run gmail-autolabel auth
```

로컬 체크아웃용 Claude Desktop 설정:

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

## 로드맵

- [ ] 50건 초과 배치 라벨링
- [ ] 시스템 프롬프트로 제공되는 라벨 추천 커스터마이징
- [ ] 헤드리스 재인증 (cron 친화)
- [ ] 구독취소/보관 자동 제안
- [ ] 다른 MCP 클라이언트 지원 (Cursor 등)

## 기여

PR 환영합니다. 큰 변경은 먼저 이슈로 논의해주세요.

## 라이선스

[MIT](LICENSE) © 2026 dr-coton
