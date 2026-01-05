#!/usr/bin/env python3
"""
Screen Description MCP Server

An MCP server that captures screenshots, saves them locally, and returns 
AI-generated descriptions. The image path is returned so it CAN be read 
if needed, but the description should be sufficient in most cases.

Usage:
    Set ANTHROPIC_API_KEY environment variable
    Configure in Cursor's MCP settings
"""

import os
import base64
import io
from datetime import datetime
from typing import Optional

import mss
import mss.tools
from PIL import Image
from mcp.server.fastmcp import FastMCP
import anthropic


# Initialize MCP server
mcp = FastMCP("screen-viewer")

# Anthropic client (initialized lazily)
_anthropic_client: Optional[anthropic.Anthropic] = None


def get_smallest_screen() -> int:
    """
    Find the screen with the smallest resolution (by pixel count).
    Excludes screen 0 (all screens combined).
    
    Returns:
        Screen number of the smallest display
    """
    with mss.mss() as sct:
        if len(sct.monitors) <= 1:
            return 1  # Only one screen available
        
        smallest_screen = 1
        smallest_pixels = float('inf')
        
        for i, monitor in enumerate(sct.monitors[1:], 1):  # Skip screen 0
            pixels = monitor['width'] * monitor['height']
            if pixels < smallest_pixels:
                smallest_pixels = pixels
                smallest_screen = i
        
        return smallest_screen


def get_anthropic_client() -> anthropic.Anthropic:
    """Get or create Anthropic client."""
    global _anthropic_client
    if _anthropic_client is None:
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError(
                "ANTHROPIC_API_KEY environment variable is required. "
                "Get your key from https://console.anthropic.com/"
            )
        _anthropic_client = anthropic.Anthropic(api_key=api_key)
    return _anthropic_client


def capture_screen(screen_num: int = 1, max_size: int = 1280) -> tuple[Image.Image, dict]:
    """
    Capture a screen and return as PIL Image.
    
    Args:
        screen_num: Screen number (0=all, 1=primary, etc.)
        max_size: Maximum dimension to resize to (for API limits)
    
    Returns:
        Tuple of (PIL Image, monitor_info)
    """
    with mss.mss() as sct:
        if screen_num < 0 or screen_num >= len(sct.monitors):
            raise ValueError(f"Screen {screen_num} not found. Available: 0-{len(sct.monitors)-1}")
        
        monitor = sct.monitors[screen_num]
        screenshot = sct.grab(monitor)
        
        # Convert to PIL Image
        img = Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")
        original_size = img.size
        
        # Resize if too large (to reduce API costs and fit limits)
        width, height = img.size
        if width > max_size or height > max_size:
            ratio = min(max_size / width, max_size / height)
            new_size = (int(width * ratio), int(height * ratio))
            img = img.resize(new_size, Image.Resampling.LANCZOS)
        
        return img, {
            "screen": screen_num,
            "original_size": f"{original_size[0]}x{original_size[1]}",
            "captured_size": f"{img.size[0]}x{img.size[1]}",
            "monitor": monitor
        }


def image_to_base64(img: Image.Image, quality: int = 85) -> str:
    """Convert PIL Image to base64 JPEG string."""
    buffer = io.BytesIO()
    img.save(buffer, format="JPEG", quality=quality)
    return base64.standard_b64encode(buffer.getvalue()).decode("utf-8")


def save_screenshot(img: Image.Image, output_dir: str, prefix: str = "screen") -> str:
    """
    Save screenshot to directory with timestamp.
    
    Args:
        img: PIL Image to save
        output_dir: Directory to save to
        prefix: Filename prefix
    
    Returns:
        Full path to saved file
    """
    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{prefix}_{timestamp}.png"
    filepath = os.path.join(output_dir, filename)
    img.save(filepath, format="PNG")
    return filepath


def describe_image_with_claude(
    base64_image: str, 
    prompt: str,
    model: str = "claude-sonnet-4-20250514"
) -> str:
    """
    Send image to Claude for description.
    
    Args:
        base64_image: Base64 encoded JPEG image
        prompt: Custom prompt for description
        model: Claude model to use
    
    Returns:
        Text description of the image
    """
    client = get_anthropic_client()
    
    message = client.messages.create(
        model=model,
        max_tokens=1024,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/jpeg",
                            "data": base64_image,
                        },
                    },
                    {
                        "type": "text",
                        "text": prompt
                    }
                ],
            }
        ],
    )
    
    return message.content[0].text


@mcp.tool()
def list_screens() -> str:
    """
    List all available screens/monitors.
    
    Returns information about each connected display including resolution and position.
    Use this to find the correct screen number for describe_screen.
    """
    smallest = get_smallest_screen()
    
    with mss.mss() as sct:
        lines = ["Available screens:"]
        for i, monitor in enumerate(sct.monitors):
            if i == 0:
                lines.append(f"  [0] All screens combined: {monitor['width']}x{monitor['height']}")
            else:
                marker = " ← smallest (default)" if i == smallest else ""
                lines.append(
                    f"  [{i}] Display {i}: {monitor['width']}x{monitor['height']} "
                    f"at position ({monitor['left']}, {monitor['top']}){marker}"
                )
        return "\n".join(lines)


@mcp.tool()
def describe_screen(
    screen_number: int = 0,
    focus: str = "general",
    save_to_directory: str = ""
) -> str:
    """
    Capture a screenshot of the specified screen and return an AI-generated description.
    
    The actual image is NOT returned - only a text summary describing what's visible.
    This is useful for understanding what the user is looking at on another monitor.
    
    Args:
        screen_number: Which screen to capture (0=all screens, 1=primary, 2=secondary, etc.)
                      Use list_screens() first to see available options.
                      Default 0 means "use the smallest screen automatically".
        focus: What to focus the description on. Options:
               - "general": Overall description of screen content
               - "code": Focus on code, programming content, errors
               - "ui": Focus on UI elements, buttons, layout
               - "text": Focus on reading and transcribing visible text
               - "browser": Focus on web content, URLs, page structure
        save_to_directory: Directory where to save the screenshot file. 
                          If empty, uses current working directory.
                          The screenshot is saved for reference but you should NOT read it 
                          unless absolutely necessary as it will significantly increase context size.
    
    Returns:
        A text description of what's visible on the screen, plus the path where the 
        screenshot was saved.
    """
    # Use smallest screen if not specified or 0
    if screen_number == 0:
        screen_number = get_smallest_screen()
    
    # Build prompt based on focus
    prompts = {
        "general": (
            "Describe what you see on this computer screen. "
            "Mention the main application(s) visible, key content, and any notable elements. "
            "Be concise but comprehensive."
        ),
        "code": (
            "This is a screenshot of a developer's screen. Focus on: "
            "1. What programming language/framework is being used "
            "2. What the code appears to be doing "
            "3. Any visible errors, warnings, or terminal output "
            "4. File names and project structure if visible "
            "Be technical and specific."
        ),
        "ui": (
            "Describe the user interface visible on this screen. "
            "Focus on: layout, main UI components, buttons, menus, forms, "
            "and the overall application structure. "
            "Describe it as if helping someone navigate the interface."
        ),
        "text": (
            "Read and transcribe the main text content visible on this screen. "
            "Focus on: headings, body text, labels, and any important messages. "
            "Organize the text logically."
        ),
        "browser": (
            "Describe this web browser screenshot. Include: "
            "1. The website/URL if visible "
            "2. Main page content and structure "
            "3. Navigation elements "
            "4. Any forms, buttons, or interactive elements "
            "5. Key text content"
        )
    }
    
    prompt = prompts.get(focus, prompts["general"])
    
    try:
        # Capture screen
        img, info = capture_screen(screen_number)
        
        # Determine save directory
        if not save_to_directory:
            save_to_directory = os.getcwd()
        
        # Save screenshot
        screenshot_path = save_screenshot(img, save_to_directory, prefix=f"screen{screen_number}")
        
        # Convert to base64 for API
        base64_image = image_to_base64(img)
        
        # Get description from Claude
        description = describe_image_with_claude(base64_image, prompt)
        
        # Format response with clear sections
        response = f"""📺 SCREEN CAPTURE RESULT
{'=' * 50}

📍 Screenshot saved to:
   {screenshot_path}

📐 Screen info:
   Screen: {info['screen']}
   Resolution: {info['original_size']}

📝 DESCRIPTION:
{'-' * 50}
{description}

{'=' * 50}
⚠️  NOTE: The screenshot file is available at the path above.
    Only read it with read_file if you need more visual detail 
    than this description provides. Reading the image will 
    significantly increase context size."""
        
        return response
        
    except ValueError as e:
        return f"Error: {str(e)}\n\nUse list_screens() to see available screens."
    except Exception as e:
        return f"Error capturing/describing screen: {str(e)}"


@mcp.tool()
def describe_screen_with_question(
    question: str,
    screen_number: int = 0,
    save_to_directory: str = ""
) -> str:
    """
    Capture a screenshot and answer a specific question about what's visible.
    
    Use this when you need to answer a specific question about what the user
    is looking at, rather than getting a general description.
    
    Args:
        question: The specific question to answer about the screen content.
                 Examples: "What error is shown?", "What file is open?", 
                          "What's the URL in the browser?"
        screen_number: Which screen to capture (default: 0 = smallest screen automatically)
        save_to_directory: Directory where to save the screenshot file.
                          If empty, uses current working directory.
    
    Returns:
        An answer to the question based on what's visible on screen.
    """
    # Use smallest screen if not specified or 0
    if screen_number == 0:
        screen_number = get_smallest_screen()
    
    prompt = (
        f"Look at this screenshot and answer the following question:\n\n"
        f"Question: {question}\n\n"
        f"Provide a direct, helpful answer based on what you can see."
    )
    
    try:
        # Capture screen
        img, info = capture_screen(screen_number)
        
        # Determine save directory
        if not save_to_directory:
            save_to_directory = os.getcwd()
        
        # Save screenshot
        screenshot_path = save_screenshot(img, save_to_directory, prefix=f"screen{screen_number}")
        
        # Convert to base64 for API
        base64_image = image_to_base64(img)
        
        # Get answer from Claude
        answer = describe_image_with_claude(base64_image, prompt)
        
        # Format response
        response = f"""📺 SCREEN Q&A RESULT
{'=' * 50}

❓ Question: {question}

📍 Screenshot saved to:
   {screenshot_path}

💬 ANSWER:
{'-' * 50}
{answer}

{'=' * 50}
⚠️  NOTE: The screenshot file is available if you need more detail.
    Avoid reading it unless necessary to preserve context space."""
        
        return response
        
    except Exception as e:
        return f"Error: {str(e)}"


if __name__ == "__main__":
    # Run the MCP server
    mcp.run()
