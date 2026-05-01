<div align="center">

# Gmail Autolabel

**为 Claude Desktop 打造的 AI 自动 Gmail 标签工具。**
不必再手动整理收件箱 —— 让 Claude 阅读、分类、归档你的邮件。

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![MCP](https://img.shields.io/badge/MCP-server-8A2BE2.svg)](https://modelcontextprotocol.io/)
[![Claude Desktop](https://img.shields.io/badge/Claude-Desktop-D97757.svg)](https://claude.ai/download)

[English](./README.md) · [한국어](./README.ko.md) · **中文** · [日本語](./README.ja.md)

<br>

<img src="./docs/hero.png" alt="经 gmail-autolabel 整理后的 Gmail 收件箱 —— 每封邮件都自动打上彩色标签" width="900">

<sub><i>Claude 整理后的收件箱:发票、安全提醒、订阅资讯、出行、工作 —— 全部自动分类,多语言邮件同样处理得当。</i></sub>

</div>

---

## 功能简介

`gmail-autolabel` 是一个 [Model Context Protocol](https://modelcontextprotocol.io/)
服务器,让 Claude Desktop 能够自动分类并为你的 Gmail 打标签。

把它接入收件箱后,Claude 会:

1. 拉取最近**没有任何用户标签**的邮件 (`has:nouserlabels`)
2. 先看主题和发件人,只有不明确时才读取正文
3. 应用已有标签,或在必要时创建新标签
4. 实在拿不准时,使用兜底标签 **"Needs Review"**(需复核)

主动权在你手里:每一次分类判断都由 Claude 根据你的提示词决定,不依赖任何
硬编码规则。可以按需运行,也可以定时调度。

## 快速演示

在 Claude Desktop 中说一句:

> 帮我整理没有标签的邮件。不清楚的就读正文。还是判断不了就打 "Needs Review"。

Claude 会执行类似流程:

```
list_labels()                            # 查看现有分类
list_unlabeled_emails(50)                # 待分类 50 封
get_email_content(<id>)                  # 仅在不明确时调用
add_label_to_email(<id>, "发票")         # 应用标签
create_label("订阅资讯")                  # 或创建新标签
```

## 与官方 Gmail MCP 的区别

|              | 官方 Gmail MCP (claude.ai)   | gmail-autolabel               |
| ------------ | ---------------------------- | ----------------------------- |
| 部署         | Anthropic 托管               | **本地运行**                  |
| OAuth 范围   | 读取 / 发送 / 修改 全权      | 仅 `gmail.modify`             |
| 发送 / 删除  | 允许                         | **不允许**                    |
| 数据流向     | 经过 Anthropic               | 直连:本机 ↔ Google         |
| 自定义       | 工具集固定                   | 代码完全在你手上              |
| 定位         | 通用 Gmail 使用              | 专注于标签分类工作流          |

如果你想要一个聚焦、透明、本地运行、最小授权的收件箱整理工具,这个项目正合适。

## 工具列表

| 工具                                          | 说明                                              |
| --------------------------------------------- | ------------------------------------------------- |
| `list_unlabeled_emails(max_results=50)`       | 没有用户标签的最新邮件 (`has:nouserlabels`)       |
| `get_email_content(email_id, max_chars=10000)` | 完整正文 (HTML 已剥离,长度限制)                  |
| `get_email_labels(email_id)`                  | 指定邮件上的标签                                  |
| `list_labels(user_only=True)`                 | 邮箱中的全部标签                                  |
| `add_label_to_email(email_id, label_name)`    | 按名称应用标签 (必须已存在)                       |
| `create_label(name)`                          | 创建标签 (幂等)                                   |

## 前置要求

- macOS 或 Linux
- Python 3.10+
- [`uv`](https://github.com/astral-sh/uv) — `brew install uv`

---

## 安装指南

### 1. 创建 Google Cloud 项目

1. 访问 <https://console.cloud.google.com/>,使用你的 Gmail 账号登录
2. 顶部项目下拉菜单 → **新建项目**
3. 名字随意 (如 `gmail-autolabel`) → **创建**
4. 创建后确认该项目处于选中状态

### 2. 启用 Gmail API

1. 侧边栏 → **API 和服务 → 库**
2. 搜索 `Gmail API` → 点击 → **启用**

### 3. 配置 OAuth 同意屏幕 ⚠️ 容易出错的步骤

1. 侧边栏 → **API 和服务 → OAuth 同意屏幕**
2. **User Type**: 选 **External** (Internal 仅限 Workspace 组织)
3. 填入应用名 (`Gmail Autolabel`)、支持邮箱、开发者邮箱。其他可选字段留空
4. **保存并继续**
5. **范围(Scopes)**: 直接 **保存并继续** —— OAuth 客户端会在运行时请求,这里不用加
6. **测试用户(Test users)**: 点 **+ ADD USERS** → 添加**自己的 Gmail 地址**
   ⚠️ 漏掉这一步会在登录时遇到 `403 access_denied`
7. **保存并继续** → 完成。让应用保持 **Testing** 状态 (见 §5)

### 4. 创建 Desktop OAuth 客户端

1. 侧边栏 → **API 和服务 → 凭据**
2. **+ 创建凭据 → OAuth 客户端 ID**
3. **应用类型: Desktop app** ← 关键,不要选 Web app
4. 名称 `gmail-autolabel-desktop` (随意)
5. **创建**,然后下载 JSON 文件
6. 移动并改名:

   ```bash
   mkdir -p ~/.config/gmail-autolabel
   mv ~/Downloads/client_secret_*.json ~/.config/gmail-autolabel/credentials.json
   ```

   想用其他路径请设置 `GMAIL_AUTOLABEL_CREDENTIALS=/path/to/credentials.json`

### 5. ⚠️ 7 天过期陷阱

处于 **Testing** 状态的应用所发放的 refresh token,**7 天后会自动过期**。
这是 Google 的策略,不是 bug。

| 选项                              | 优点                | 缺点                                                          |
| --------------------------------- | ------------------- | ------------------------------------------------------------- |
| **A. 保持 Testing,每周重新认证** | 免费,即用          | 每周一条命令                                                  |
| **B. 发布到 Production**          | Token 永不过期      | `gmail.modify` 是受限范围 → 需要 Google 审核                  |
| **C. Workspace + Internal 类型**  | 无需审核,无限期    | 需要付费的 Google Workspace                                   |

**推荐选 A。** Token 过期时一行命令即可恢复 (见 §重新认证)。

### 6. 首次 OAuth 认证

```bash
uvx --from git+https://github.com/dr-coton/gmail-autolabel gmail-autolabel auth
```

执行流程:

1. 本地启动一个临时 HTTP 服务器 (随机端口)
2. 浏览器自动打开 Google 登录页
3. 选择你的 Gmail 账号
4. 出现 **"Google 尚未验证此应用"** 警告 —— 这是正常的。
   点 **高级** → **前往 Gmail Autolabel(不安全)**
5. 授权 → 浏览器跳回 localhost
6. 终端打印 `Authentication complete. Token saved to ...`

Token 存放在 `~/.config/gmail-autolabel/token.json`。

### 7. 配置 Claude Desktop

打开配置文件:

```bash
open -e ~/Library/Application\ Support/Claude/claude_desktop_config.json
```

加入 `mcpServers` 条目 (与已有配置合并):

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

保存 → **完全退出 Claude Desktop (⌘Q) 后重新启动**。

### 8. 验证

在 Claude Desktop 新建对话,点击工具图标,应能看到 `gmail-autolabel` 及 6 个工具:

> 列出我的 Gmail 标签

如果 `list_labels` 返回结果,就说明成功了。

---

## 重新认证

Token 过期时 (Testing 模式下每 7 天一次),用一行命令恢复:

```bash
uvx --from git+https://github.com/dr-coton/gmail-autolabel gmail-autolabel auth --force
```

`--force` (别名 `--refresh`) 做的事:

- 删除现有的 `token.json`
- 向 Google 发送 `prompt=consent`,强制颁发新的 refresh token

不带 `--force` 时,Google 可能缓存之前的同意,只发新的 access token,
导致一周后再次出现同样的过期问题。恢复时建议用 `--force`。

## 更新

`uvx` 会缓存 git URL。拉取新版本:

```bash
uvx --refresh --from git+https://github.com/dr-coton/gmail-autolabel gmail-autolabel --help
```

同时刷新缓存 + 重新认证:

```bash
uvx --refresh --from git+https://github.com/dr-coton/gmail-autolabel gmail-autolabel auth --force
```

## 权限范围

仅请求 `https://www.googleapis.com/auth/gmail.modify` —— 读取邮件 + 修改标签。
**不能** 发送邮件、删除邮件或更改账号设置。

随时可在此撤销授权: <https://myaccount.google.com/permissions>

## 故障排查

| 错误                                              | 原因 / 解决                                                          |
| ------------------------------------------------- | -------------------------------------------------------------------- |
| `403 access_denied` (浏览器中)                    | 邮箱未加入 Test users → §3 第 6 步                                   |
| `redirect_uri_mismatch`                           | OAuth client 创建为 Web app → 重新创建为 **Desktop app**             |
| `invalid_grant: Token has been expired or revoked` | 7 天过期 → 运行 `gmail-autolabel auth --force`                     |
| `Token not found` (MCP 启动时)                    | 认证未完成 → 重新执行 §6                                             |
| Claude Desktop 看不到工具                         | 配置 JSON 语法错误,或没有完全重启                                   |
| `uvx: command not found`                          | `brew install uv`                                                    |
| 查看 MCP 日志                                     | `~/Library/Logs/Claude/mcp*.log`                                     |

## 本地开发

```bash
git clone https://github.com/dr-coton/gmail-autolabel
cd gmail-autolabel
uv sync
uv run gmail-autolabel auth
```

本地版的 Claude Desktop 配置:

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

## 路线图

- [ ] 单次运行支持 50 封以上的批量标签
- [ ] 通过系统提示自定义标签建议规则
- [ ] 无头重新认证 (适配 cron)
- [ ] 智能退订 / 归档建议
- [ ] 支持其他 MCP 客户端 (Cursor 等)

## 贡献

欢迎 PR。较大的改动请先开 issue 讨论。

## 许可证

[MIT](LICENSE) © 2026 dr-coton
