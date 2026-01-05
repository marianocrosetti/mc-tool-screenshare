# Screen Capture for AI Agents

Let your AI agent see your screen. No more manual screenshots.

## 1. Install

```bash
git clone https://github.com/marianocrosetti/mc-tool-screenshare.git
cd mc-tool-screenshare
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

> ⚠️ **macOS**: Grant screen recording permission to your terminal in System Preferences → Privacy & Security → Screen Recording

## 2. Add the Agent Rule

Copy this to `.cursor/rules/screen-capture.mdc`:

```markdown
# Screen Capture Tool

Use this tool to capture screenshots of the user's screen. Read the output image with read_file.

\`\`\`bash
/path/to/mc-tool-screenshare/.venv/bin/python \
  /path/to/mc-tool-screenshare/screen_capture.py \
  <SCREEN_NUMBER> --fast -o <OUTPUT_DIRECTORY>
\`\`\`

Use "all" permissions (sandbox blocks screen capture).

- `SCREEN_NUMBER`: 1 = primary, 2 = secondary
- `OUTPUT_DIRECTORY`: Where to save (agent must be able to read it)
```

## 3. (Optional) Use as MCP Server

Add to Cursor MCP settings for AI-powered descriptions:

```json
{
  "mcpServers": {
    "screen-viewer": {
      "command": "/path/to/mc-tool-screenshare/.venv/bin/python",
      "args": ["/path/to/mc-tool-screenshare/screen_mcp_server.py"],
      "env": {
        "ANTHROPIC_API_KEY": "your-key"
      }
    }
  }
}
```

This adds tools like `describe_screen` and `describe_screen_with_question`.
