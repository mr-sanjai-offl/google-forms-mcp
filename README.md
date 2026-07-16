```text
  ______       ________                                              __       __  ______  _______  
 /      \     |        \                                            |  \     /  \/      \|       \ 
|  ▓▓▓▓▓▓\    | ▓▓▓▓▓▓▓▓ ______   ______  ______ ____   _______     | ▓▓\   /  ▓▓  ▓▓▓▓▓▓\ ▓▓▓▓▓▓▓\
| ▓▓ __\▓▓    | ▓▓__    /      \ /      \|      \    \ /       \    | ▓▓▓\ /  ▓▓▓ ▓▓   \▓▓ ▓▓__/ ▓▓
| ▓▓|    \    | ▓▓  \  |  ▓▓▓▓▓▓\  ▓▓▓▓▓▓\ ▓▓▓▓▓▓\▓▓▓▓\  ▓▓▓▓▓▓▓    | ▓▓▓▓\  ▓▓▓▓ ▓▓     | ▓▓    ▓▓
| ▓▓ \▓▓▓▓    | ▓▓▓▓▓  | ▓▓  | ▓▓ ▓▓   \▓▓ ▓▓ | ▓▓ | ▓▓\▓▓    \     | ▓▓\▓▓ ▓▓ ▓▓ ▓▓   __| ▓▓▓▓▓▓▓ 
| ▓▓__| ▓▓    | ▓▓     | ▓▓__/ ▓▓ ▓▓     | ▓▓ | ▓▓ | ▓▓_\▓▓▓▓▓▓\    | ▓▓ \▓▓▓| ▓▓ ▓▓__/  \ ▓▓      
 \▓▓    ▓▓    | ▓▓      \▓▓    ▓▓ ▓▓     | ▓▓ | ▓▓ | ▓▓       ▓▓    | ▓▓  \▓ | ▓▓\▓▓    ▓▓ ▓▓      
  \▓▓▓▓▓▓      \▓▓       \▓▓▓▓▓▓ \▓▓      \▓▓  \▓▓  \▓▓\▓▓▓▓▓▓▓      \▓▓      \▓▓ \▓▓▓▓▓▓ \▓▓      
                                                             
```

# Google Forms MCP

[![Release v1.0.0](https://img.shields.io/badge/release-v1.0.0-purple.svg)](https://github.com/your-org/google-forms-mcp/releases/tag/v1.0.0)
[![PyPI version](https://img.shields.io/badge/pypi-v1.0.0-blue.svg)](https://pypi.org/project/google-forms-mcp/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![MCP Protocol](https://img.shields.io/badge/MCP-Compatible-green.svg)](https://modelcontextprotocol.io)
[![Docker Support](https://img.shields.io/badge/Docker-Ready-blue.svg)](https://www.docker.com/)

**Production-grade Model Context Protocol (MCP) server for Google Forms, Drive, and Sheets automation.**

Create, manage, and analyze Google Forms through an autonomous AI Planner that works with Claude, ChatGPT, Cursor, VS Code, Windsurf, Cline, Roo Code, and any MCP-compatible client.

---

## ✨ Features

### 🤖 Autonomous AI Planner (`plan_form`, `get_template`, `validate_execution_plan`)
- Automatically detects user intent and interviews the user for missing details.
- Validates the execution plan to prevent API errors and mutually exclusive field conflicts.
- Orchestrates Google Forms tools automatically to build complex forms.
- Includes pre-built templates (`Hackathon`, `Survey`, `Quiz`, `RSVP`).

### 📝 Form Management
- **Create** forms with title, description, and quiz mode
- **Update** form metadata and settings (progress bar, email collection, shuffle questions)
- **Delete** / **Duplicate** / **Publish** forms
- **Search** for forms in Google Drive

### ❓ All 11 Question Types Supported
- `SHORT_ANSWER`, `PARAGRAPH`, `MULTIPLE_CHOICE`, `CHECKBOXES`, `DROPDOWN`
- `FILE_UPLOAD`, `LINEAR_SCALE`, `DATE`, `TIME`
- `MULTIPLE_CHOICE_GRID`, `CHECKBOX_GRID`

### 📑 Sections & Layout
- Add, update, delete sections (page breaks) with conditional navigation
- Add images, videos, and text blocks

### 🧪 Quiz Mode
- Enable quiz grading with point values
- Set answer keys with correct answers and right/wrong feedback

### 📊 Response & Analytics Management
- Read all form responses (paginated) (`get_responses`, `get_response`)
- Get aggregated response summary statistics (`get_response_summary`)
- Export responses as CSV or JSON (`export_responses`)

### 📁 Google Drive Integration
- Create folders, move/copy/trash files, and search specific forms
- Manage permissions and share files with users, groups, or domains

### 📈 Google Sheets Integration
- Create spreadsheets, read/write/append data ranges, and export to CSV

---

## 🚀 Quickstart

### 1. Google Cloud Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project (or select an existing one)
3. Go to **APIs & Services → Library** and enable these APIs:
   - **Google Forms API**
   - **Google Drive API**
   - **Google Sheets API**
4. Go to **APIs & Services → Credentials**
5. Create an **OAuth 2.0 Client ID**:
   - Application type: **Desktop application**
   - Name: `Google Forms MCP`
6. Note down your **Client ID** and **Client Secret**.

---

### 2. Get a Refresh Token (`generate_token.py`)

We provide an interactive, self-troubleshooting token generator helper script right inside the repository:

```bash
# Run interactively (will prompt for Client ID and Secret if not set)
python generate_token.py

# Or pass directly via command line arguments
python generate_token.py --client-id "your-client-id" --client-secret "your-client-secret"

# Or pass the downloaded JSON secrets file from GCP
python generate_token.py --file client_secret.json
```

The script will launch your browser, complete authentication, output your `GOOGLE_REFRESH_TOKEN`, and automatically offer to save it directly into your local `.env` file!

#### 💡 Token Generator Troubleshooting (`generate_token.py`)
If you encounter issues generating your refresh token, check the common fixes below:

* **Error 400 (`redirect_uri_mismatch`)**:
  1. Go to Google Cloud Console -> **APIs & Services -> Credentials**.
  2. Click on your **OAuth 2.0 Client ID**.
  3. Under **Authorized redirect URIs**, click **+ ADD URI** and add exactly:
     `http://localhost:8080/`
  4. Click **Save**, wait 30–60 seconds for Google's servers to sync, and re-run `python generate_token.py --port 8080`.

* **Access Blocked (`This app's request is invalid` / Error 403)**:
  1. Go to Google Cloud Console -> **APIs & Services -> OAuth consent screen**.
  2. If your app publishing status is set to **Testing**, scroll down to **Test users**.
  3. Click **+ ADD USERS** and enter the exact Google email address you are logging in with.

* **No Refresh Token Returned**:
  1. Go to [Google Account Connections](https://myaccount.google.com/connections).
  2. Click on `Google Forms MCP` and select **Remove Access**.
  3. Re-run `python generate_token.py` to prompt for a fresh offline token.

---

### 3. Install & Run

```bash
# Using uvx (recommended for instant execution)
uvx google-forms-mcp

# Or install from source locally using uv / pip
git clone https://github.com/your-org/google-forms-mcp.git
cd google-forms-mcp
uv sync
uv run python -m google_forms_mcp

# Or run as a standalone HTTP server (Streamable HTTP transport on port 8000)
export GOOGLE_FORMS_MCP_TRANSPORT="http"
python -m google_forms_mcp
```

---

### 4. Configure Your MCP Client

#### Option A: Running from Local Git Cloned Source (Include `"cwd"`)
If you cloned this repository locally, **you must include the `"cwd"` property** so your client locates the project environment (`.env`) and Python executable cleanly:

```json
{
  "mcpServers": {
    "google-forms": {
      "command": "python",
      "args": ["-m", "google_forms_mcp"],
      "cwd": "C:/absolute/path/to/google-forms-mcp",
      "env": {
        "GOOGLE_CLIENT_ID": "your-client-id",
        "GOOGLE_CLIENT_SECRET": "your-client-secret",
        "GOOGLE_REFRESH_TOKEN": "your-refresh-token"
      }
    }
  }
}
```

#### Option B: Running via PyPI (`uvx`)
If running globally without cloning:

```json
{
  "mcpServers": {
    "google-forms": {
      "command": "uvx",
      "args": ["google-forms-mcp"],
      "env": {
        "GOOGLE_CLIENT_ID": "your-client-id",
        "GOOGLE_CLIENT_SECRET": "your-client-secret",
        "GOOGLE_REFRESH_TOKEN": "your-refresh-token"
      }
    }
  }
}
```

#### Option C: Connecting via Custom Connector (Claude Web / Remote HTTP)
If running the server in `http` transport mode on `http://127.0.0.1:8000/mcp`:
1. Open your MCP Client connector settings.
2. Enter **Remote MCP server URL**: `http://127.0.0.1:8000/mcp` *(Or your public HTTPS tunnel URL if connecting from cloud web apps like `claude.ai`)*.
3. Leave OAuth settings blank if your `.env` already contains `GOOGLE_REFRESH_TOKEN`.

---

## 🔧 Available Tools (44 Tools Total)

### AI Planner & Prompts (3 tools)
| Tool | Description |
|:-----|:------------|
| `plan_form` | Interview user and autonomously outline form questions |
| `get_template` | Get pre-built JSON form templates (`Hackathon`, `Survey`, `Quiz`, `RSVP`) |
| `validate_execution_plan` | Validate question sequence and rules before API execution |

### Forms (19 tools)
| Tool | Description |
|:-----|:------------|
| `create_form` | Create a new Google Form |
| `get_form` | Retrieve complete form structure |
| `update_form_info` | Update title and description |
| `delete_form` | Delete (trash or permanent) |
| `duplicate_form` | Copy an existing form |
| `publish_form` | Publish or stop accepting responses |
| `add_question` | Add any of the 11 question types |
| `update_question` | Modify an existing question |
| `delete_question` | Remove a question |
| `move_question` | Reorder a question |
| `duplicate_question` | Duplicate an existing question |
| `set_question_branching` | Branch based on choice option |
| `add_section` | Add a section (page break) |
| `update_section` | Update section title/description |
| `delete_section` | Remove a section |
| `set_section_navigation` | Set section navigation action |
| `update_settings` | Update form settings (quiz, progress bar, etc.) |
| `add_media` | Add an image or video |
| `add_text_item` | Add a text block |

### Responses & Analytics (4 tools)
| Tool | Description |
|:-----|:------------|
| `get_responses` | List all responses (paginated) |
| `get_response` | Get a single response by ID |
| `get_response_summary` | Aggregated statistics across all questions |
| `export_responses` | Export as CSV or JSON |

### Drive (12 tools)
| Tool | Description |
|:-----|:------------|
| `create_folder` | Create a Drive folder |
| `search_forms` | Search specifically for Google Forms |
| `search_files` | Search for any files |
| `move_file` | Move to another folder |
| `copy_file` | Copy a file |
| `trash_file` | Move to trash |
| `restore_file` | Restore from trash |
| `get_file_metadata` | Get complete file metadata |
| `share_file` | Share with users/groups |
| `transfer_ownership` | Transfer file ownership |
| `get_permissions` | List sharing permissions |
| `remove_permission` | Remove a permission |

### Sheets (7 tools)
| Tool | Description |
|:-----|:------------|
| `create_spreadsheet` | Create a new spreadsheet |
| `get_spreadsheet_info` | Get spreadsheet metadata |
| `read_sheet_data` | Read from a range |
| `write_sheet_data` | Write to a range |
| `append_sheet_data` | Append rows |
| `clear_sheet_data` | Clear data from a range |
| `export_sheet_csv` | Export as CSV |

---

## ⚙️ Configuration

| Environment Variable | Description | Default |
|:----|:----|:----|
| `GOOGLE_CLIENT_ID` | OAuth 2.0 Client ID | Required |
| `GOOGLE_CLIENT_SECRET` | OAuth 2.0 Client Secret | Required |
| `GOOGLE_REFRESH_TOKEN` | Pre-obtained Refresh Token | Required |
| `GOOGLE_CLIENT_SECRETS_FILE` | Path to client secrets JSON | — |
| `GOOGLE_FORMS_MCP_TRANSPORT` | Transport mode: `stdio` or `http` | `stdio` |
| `GOOGLE_FORMS_MCP_PORT` | HTTP port (when transport=http) | `8000` |
| `GOOGLE_FORMS_MCP_LOG_LEVEL` | Log level | `INFO` |
| `GOOGLE_FORMS_MCP_TOKEN_PATH` | Token storage path | `~/.google-forms-mcp/token.json` |

---

## ⚠️ Known Limitations

These are Google Forms API limitations, not limitations of this MCP:

| Feature | Status |
|:--------|:-------|
| Theme customization (colors, fonts, headers) | ❌ Not supported by API |
| Delete responses | ❌ Not supported by API |
| Link Form to Sheets | ❌ Not supported via API (requires UI/Apps Script) |
| Settings | ✅ Now fully supported |

---

## 🤝 Contributing

Contributions are welcome! See `CONTRIBUTING.md` for guidelines.

```bash
# Clone the repo
git clone https://github.com/your-org/google-forms-mcp.git
cd google-forms-mcp

# Install dependencies
uv sync --dev

# Run tests
uv run pytest

# Lint & format
uv run ruff check src/ tests/
uv run ruff format src/ tests/
```

---

## 📄 License

MIT License — see `LICENSE` for details.
