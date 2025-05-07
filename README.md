# Manim Animator from Prompt

## Project Description

Manim Animator is a Python application that leverages the Anthropic Claude API to generate Manim animations directly from natural language text prompts. You describe the animation you want, and the tool orchestrates the generation of a Manim script and its subsequent rendering into a video.

## How It Works

1.  **Prompt Input**: The user provides a text prompt via a command-line argument, describing the desired animation (e.g., "Create a blue circle that transforms into a red square").
2.  **Script Generation (via Claude API)**:
    *   The application constructs a detailed system prompt, instructing the Claude API (`claude-3-7-sonnet-latest` model) to act as a Manim programming expert.
    *   This prompt, along with the user's animation description, is sent to the Claude API.
    *   The API returns a complete, runnable Python script for the Manim Community edition.
    *   The script typically includes necessary imports (`manim import *`, `import numpy as np`) and a scene class inheriting from `manim.Scene` with the animation logic in its `construct` method.
    *   The application performs minor cleanup on the returned script, such as removing Markdown code block delimiters.
3.  **Script Saving**: The generated Manim script is saved locally (e.g., as `generated_manim_scene.py`).
4.  **Manim Rendering**:
    *   The application then invokes the `manim` command-line tool.
    *   It passes the generated script, scene name, and user-specified options (like quality, preview mode, silent operation) to Manim.
    *   Manim renders the animation based on the script.
5.  **Output**: The path to the final rendered video file (typically an MP4) is displayed to the user. If errors occur during generation or rendering, they are printed to the console.

## Command-Line Usage

You can run the application from your terminal using `python main.py`.

**Arguments:**

*   `--prompt TEXT`: (Required) The text prompt describing the animation.
*   `--output_script TEXT`: Filename for the generated Manim script. (Default: `generated_manim_scene.py`)
*   `--scene_name TEXT`: Name of the Manim scene in the script. (Default: `PromptAnimationScene`)
*   `--quality {l,m,h,k}`: Rendering quality.
    *   `l`: Low (480p15)
    *   `m`: Medium (720p30)
    *   `h`: High (1080p60)
    *   `k`: 4K (2160p60)
    (Default: `l`)
*   `--preview`: If set, previews the animation after rendering (opens the video).
*   `--silent`: If set, runs Manim with less verbose output.

**Example:**

```bash
python main.py \
    --prompt "Show a green square appearing on the left, then a blue circle appearing on the right. Finally, transform the square into a triangle and the circle into a star." \
    --output_script my_animation_scene.py \
    --scene_name MyCustomAnimation \
    --quality m \
    --preview
```

**Prerequisites:**

*   Python 3.x
*   Manim Community Edition: Ensure `manim` is installed and accessible in your system's PATH.
*   Anthropic Python SDK: Install using `uv pip install anthropic`.
*   Anthropic API Key: You need to have an `ANTHROPIC_API_KEY` environment variable set up for the Claude API calls to work.

**Features:**

*   Uses Claude 3.7 Sonnet for high-quality script generation
*   Increased token limit (16000) for complete script generation
*   Robust error handling for API and rendering issues
*   Support for complex animations with proper cleanup and timing
*   Multiple quality options for different use cases
