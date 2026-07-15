# 🟣 Google Forms MCP

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![MCP Protocol](https://img.shields.io/badge/MCP-Compatible-green.svg)](https://modelcontextprotocol.io)
[![CI](https://github.com/your-org/google-forms-mcp/actions/workflows/ci.yml/badge.svg)](https://github.com/your-org/google-forms-mcp/actions/workflows/ci.yml)
[![Docker Support](https://img.shields.io/badge/Docker-Ready-blue.svg)](https://www.docker.com/)

**Production-grade Model Context Protocol (MCP) server for Google Forms automation.**

Create, manage, and analyze Google Forms through an autonomous AI Planner that works with Claude, ChatGPT, Cursor, VS Code, Windsurf, Cline, Roo Code, and any MCP-compatible client.

---

## ✨ Features

### 🤖 Autonomous AI Planner
- Automatically detects user intent and interviews the user for missing details.
- Validates the execution plan to prevent API errors.
- Orchestrates Google Forms tools automatically to build complex forms.
- Includes pre-built templates (Hackathon, Survey, Quiz, RSVP).

### 📝 Form Management
- **Create** forms with title, description, and quiz mode
- **Update** form metadata and settings
- **Delete** / **Duplicate** / **Publish** forms
- **Search** for forms in Google Drive

### ❓ All 11 Question Types
- Short Answer, Paragraph, Multiple Choice, Checkboxes, Dropdown
- File Upload, Linear Scale, Date, Time
- Multiple Choice Grid, Checkbox Grid

### 📑 Sections & Layout
- Add, update, delete sections (page breaks)
- Add images, videos, and text blocks

### 🧪 Quiz Mode
- Enable quiz grading with point values
- Set answer keys with correct answers
- Configure right/wrong feedback

### 📊 Response Management
- Read all form responses (paginated)
- Get response summary statistics
- Export as CSV or JSON

### 📁 Google Drive Integration
- Create folders, move/copy/trash files
- Search files and forms
- Share with users, groups, or domains
- Manage permissions

### 📈 Google Sheets Integration
- Create spreadsheets
- Read, write, and append data
- Export sheets as CSV

---

## 🚀 Quickstart

### 1. Google Cloud Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project (or select existing)
3. Enable these APIs:
   - **Google Forms API**
   - **Google Drive API**
   - **Google Sheets API**
4. Go to **APIs & Services → Credentials**
5. Create **OAuth 2.0 Client ID** (Desktop application)
6. Download the credentials or note the Client ID and Client Secret

### 2. Get a Refresh Token

Use the [Google OAuth Playground](https://developers.google.com/oauthplayground/) or the built-in auth flow:

```bash
# Option A: Use environment variables with a pre-obtained refresh token
export GOOGLE_CLIENT_ID="your-client-id"
export GOOGLE_CLIENT_SECRET="your-client-secret"
export GOOGLE_REFRESH_TOKEN="your-refresh-token"

# Option B: Interactive flow (opens browser)
export GOOGLE_CLIENT_SECRETS_FILE="path/to/client_secret.json"
```

### 3. Install & Run

```bash
# Using uvx (recommended)
uvx google-forms-mcp

# Using pip
pip install google-forms-mcp
python -m google_forms_mcp

# Using Docker Compose
docker-compose up -d
```

### 4. Configure Your MCP Client

#### Claude Desktop

Add to `claude_desktop_config.json`:

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

#### Cursor / VS Code / Windsurf

Add to your MCP settings:

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

#### Cline / Roo Code

Add to your `cline_mcp_settings.json`:

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

---

## 🔧 Available Tools (38 tools)

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

### Responses (4 tools)

| Tool | Description |
|:-----|:------------|
| `get_responses` | List all responses (paginated) |
| `get_response` | Get a single response by ID |
| `get_response_summary` | Aggregated statistics |
| `export_responses` | Export as CSV or JSON |

### Drive (12 tools)

| Tool | Description |
|:-----|:------------|
| `create_folder` | Create a Drive folder |
| `search_forms` | Search for Google Forms |
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

Contributions are welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

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

MIT License — see [LICENSE](LICENSE) for details.
