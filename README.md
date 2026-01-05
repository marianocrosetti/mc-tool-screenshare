# mc-tool-screenshare

An MCP (Model Context Protocol) server that captures screenshots and returns AI-generated descriptions. Perfect for helping Cursor understand what you're looking at on another monitor.

## Features

- **📺 List Screens**: See all available monitors and their resolutions
- **📝 Describe Screen**: Capture a screenshot and get an AI description (general, code, UI, text, or browser focus)
- **❓ Q&A Mode**: Ask specific questions about what's visible on screen

## Prerequisites

1. **Python 3.10+**
2. **Anthropic API Key** (for Claude vision): Get one at https://console.anthropic.com/

## Installation

1. **Clone/download this repository**

2. **Create a virtual environment and install dependencies**:

```bash
cd /Users/marianocrosetti/Desktop/mc-tool-screenshare
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

3. **Grant screen recording permissions** (macOS):
   - Go to **System Preferences → Privacy & Security → Screen Recording**
   - Add your terminal app (Terminal, iTerm, or Cursor) to the allowed list

## Connecting to Cursor

### Step 1: Open Cursor MCP Settings

1. Open Cursor
2. Press `Cmd + Shift + P` (macOS) or `Ctrl + Shift + P` (Windows/Linux)
3. Type "Cursor Settings" and select **Cursor Settings: Open Cursor Settings**
4. Navigate to the **MCP** section in the sidebar

### Step 2: Add the MCP Server Configuration

Click "Add new MCP server" or edit the configuration file directly. Add the following configuration:

**Option 1: Using Doppler (Recommended)**

This uses Doppler to inject the `ANTHROPIC_API_KEY` from the `ai-service` project:

```json
{
  "mcpServers": {
    "screen-viewer": {
      "command": "doppler",
      "args": [
        "run",
        "--project", "ai-service",
        "--config", "dev",
        "--",
        "/Users/marianocrosetti/Desktop/mc-tool-screenshare/.venv/bin/python",
        "/Users/marianocrosetti/Desktop/mc-tool-screenshare/screen_mcp_server.py"
      ]
    }
  }
}
```

**Option 2: Direct API Key**

If you prefer to set the key directly:

```json
{
  "mcpServers": {
    "screen-viewer": {
      "command": "/Users/marianocrosetti/Desktop/mc-tool-screenshare/.venv/bin/python",
      "args": [
        "/Users/marianocrosetti/Desktop/mc-tool-screenshare/screen_mcp_server.py"
      ],
      "env": {
        "ANTHROPIC_API_KEY": "your-anthropic-api-key-here"
      }
    }
  }
}
```

### Step 3: Restart Cursor

After saving the configuration, restart Cursor to load the new MCP server.

### Step 4: Verify Connection

Once connected, you should see the `screen-viewer` server in your MCP panel. The following tools will be available:

| Tool | Description |
|------|-------------|
| `list_screens` | List all available screens/monitors |
| `describe_screen` | Capture and describe a screen (with focus options) |
| `describe_screen_with_question` | Capture screen and answer a specific question |

## Usage Examples

Once connected, you can ask Cursor things like:

- "What's on my second monitor?"
- "Describe the code on screen 2"
- "What error is showing on my other screen?"
- "Read the text visible on screen 1"
- "What URL is open in the browser on screen 2?"

## Available Tools

### `list_screens()`
Lists all connected monitors with their resolutions and positions.

### `describe_screen(screen_number, focus, save_to_directory)`
- `screen_number`: Which screen (0=all, 1=primary, 2=secondary...)
- `focus`: What to emphasize in the description:
  - `"general"` - Overall screen content
  - `"code"` - Programming content, errors, terminal output
  - `"ui"` - UI elements, buttons, layout
  - `"text"` - Read and transcribe visible text
  - `"browser"` - Web content, URLs, page structure
- `save_to_directory`: Where to save the screenshot file

### `describe_screen_with_question(question, screen_number, save_to_directory)`
Ask a specific question about what's visible on the screen.

## Standalone Screen Capture (Optional)

For simple screenshot capture without AI descriptions:

```bash
python screen_capture.py              # Screen 1, every 3 seconds
python screen_capture.py 2            # Screen 2, every 3 seconds  
python screen_capture.py 1 5          # Screen 1, every 5 seconds
python screen_capture.py 1 3 10       # Screen 1, every 3s, max 10 shots
python screen_capture.py -l           # List available screens
```

## Troubleshooting

### "Screen recording permission denied"
- macOS: Add your terminal/Cursor to Screen Recording permissions in System Preferences
- May need to restart the app after granting permission

### "ANTHROPIC_API_KEY not set"
- Ensure the API key is set in the MCP configuration or as an environment variable
- Verify the key is valid at https://console.anthropic.com/

### "Server not appearing in Cursor"
- Check the configuration JSON syntax is valid
- Ensure the Python path points to the venv Python executable
- Look for errors in Cursor's MCP panel

### "Module not found" errors
- Make sure you're using the venv Python: `.venv/bin/python`
- Reinstall dependencies: `pip install -r requirements.txt`

## Project Structure

```
mc-tool-screenshare/
├── README.md                 # This file
├── requirements.txt          # Python dependencies
├── screen_mcp_server.py      # MCP server with AI-powered screen tools
├── screen_capture.py         # Standalone screenshot utility
├── screen_share_cli.py       # CLI utilities
└── screen_share_demo.py      # Demo script
```

## License

MIT
