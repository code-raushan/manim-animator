# manim_from_prompt.py
# A Python application to generate Manim animations from text prompts.

import argparse
import subprocess
import os
import re
import shlex

# --- Configuration ---
DEFAULT_SCRIPT_FILENAME = "generated_manim_scene.py"
DEFAULT_SCENE_NAME = "PromptAnimationScene"
DEFAULT_QUALITY = "l" # l (low), m (medium), h (high), k (4k)

# Manim specific color mapping (simplified)
# Manim uses constants like BLUE, RED, etc.
# We'll try to map common color names to these.
# This can be expanded significantly.
COLOR_MAP = {
    "red": "RED",
    "blue": "BLUE",
    "green": "GREEN",
    "yellow": "YELLOW",
    "orange": "ORANGE",
    "pink": "PINK",
    "purple": "PURPLE",
    "teal": "TEAL",
    "gold": "GOLD",
    "white": "WHITE",
    "black": "BLACK",
    "gray": "GRAY",
    "lightgray": "LIGHT_GRAY", # Corrected Manim constant
    "darkgray": "DARK_GRAY",   # Corrected Manim constant
    # ... add more colors as needed
}

# Supported Manim Mobjects
SUPPORTED_SHAPES = {
    "circle": "Circle",
    "square": "Square",
    "triangle": "Triangle",
    "dot": "Dot",
    "line": "Line",
    "rectangle": "Rectangle",
    "ellipse": "Ellipse",
    "arrow": "Arrow",
}

# Supported Manim Animations
SUPPORTED_ANIMATIONS = {
    "create": "Create",
    "write": "Write",
    "draw": "Create", # Alias for Create
    "show": "Create", # Alias for Create
    "appear": "FadeIn",
    "fadein": "FadeIn",
    "fadeout": "FadeOut",
    "transform": "Transform",
    "move": "animate", # Special handling for .animate syntax
    "shift": "shift", # Method for mobjects
    "scale": "scale", # Method for mobjects
    "rotate": "rotate", # Method for mobjects
}

class ManimRunner:
    """
    Saves the Manim script and runs the Manim CLI to render the video.
    """
    def run(self, script_content, script_filename, scene_name, quality, preview, silent):
        try:
            with open(script_filename, "w") as f:
                f.write(script_content)
            print(f"Manim script saved to: {script_filename}")

            # Construct Manim command
            # Example: manim -pql script_filename SceneName
            command = ["manim"]
            if preview:
                command.append("-p") # Preview flag

            quality_flag = f"-q{quality}"
            command.append(quality_flag)

            if silent:
                command.append("--progress_bar") # Show progress bar but less verbose
                command.append("none") # Suppress media player opening if -p is also used with silent
                                       # Or use --quiet, but that might hide errors.
                                       # A better way for silent might be to redirect stdout/stderr.

            command.append(script_filename)
            command.append(scene_name)

            print(f"Running Manim: {' '.join(shlex.quote(c) for c in command)}")

            # Execute Manim
            # Set MANIM_INTERACTIVE=True for -p to work reliably on some systems.
            env = os.environ.copy()
            env["MANIM_INTERACTIVE"] = "True"
            process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=env)
            stdout, stderr = process.communicate()

            if process.returncode == 0:
                print("Manim rendering successful!")
                print("Output from Manim:")
                print(stdout)
                # Try to find the video file path (Manim has a standard output structure)
                # media/videos/script_filename_without_ext/quality/SceneName.mp4
                script_base = os.path.splitext(script_filename)[0]
                # Manim output folder structure can vary slightly based on version/config
                # Common structure: media/videos/<script_name_no_ext>/<quality_dir>/<scene_name>.mp4
                # quality_dir examples: 1080p60, 720p30, 480p15 etc.
                # The quality flag -ql gives 480p15, -qm gives 720p30, -qh gives 1080p60, -qk gives 2160p60
                quality_dirs = {
                    "l": "480p15", "m": "720p30", "h": "1080p60", "k": "2160p60"
                }
                video_path = os.path.join("media", "videos", script_base, quality_dirs.get(quality, "480p15"), f"{scene_name}.mp4")
                if os.path.exists(video_path):
                    print(f"Video saved to: {os.path.abspath(video_path)}")
                    return os.path.abspath(video_path)
                else:
                    print(f"Could not automatically find video file. Check Manim output above or the 'media/videos/{script_base}/' directory.")
                    return None
            else:
                print("Error during Manim rendering:")
                print("STDOUT:")
                print(stdout)
                print("STDERR:")
                print(stderr)
                return None

        except FileNotFoundError:
            print("Error: Manim command not found. Please ensure Manim is installed and in your PATH.")
            return None
        except Exception as e:
            print(f"An error occurred: {e}")
            return None

# --- Main Application Logic ---

def generate_manim_script_with_anthropic(user_prompt, scene_name):
    """
    Generates a Manim Python script using the Anthropic Claude model.
    """
    print(f"Generating Manim script for prompt: '{user_prompt}' using Anthropic Claude model...")

    # Construct a detailed prompt for the Claude model
    # This prompt guides the model to produce a valid Manim script.
    # Claude typically uses a system prompt.
    system_prompt = '''
You are an expert Manim programmer. Your task is to take a natural language prompt
from a user and convert it into a *fully implemented, complete, and error-free*, runnable Python script for Manim Community edition.

The script should contain one class named '{scene_name}' that inherits from 'manim.Scene'.
All animation logic must be within the 'construct' method of this class.
Ensure all necessary Manim objects are imported (e.g., from 'manim import *').
Include 'import numpy as np' if complex positioning or math is likely needed.

**Important Instructions for Code Generation:**
1.  **Produce only the Python code** for the Manim script. Do not include any explanations, markdown formatting, or any text other than the script itself.
2.  The script must be **ready to be saved to a .py file and executed directly without any modifications or runtime errors.**
3.  **Implement all aspects of the user's prompt.** Do not leave any parts of the animation unimplemented.
4.  **Do NOT use placeholder comments** (e.g., "# ... TODO ...", "# ... add code here ...", "# Placeholder for ..."). The generated script must be complete.
5.  If the user prompt implies multiple scenes, steps, or complex sequences, **ensure all are fully coded within the `construct` method.**
6.  **Pay close attention to indexing for Mobjects, especially `MathTex` objects.** 
    *   When working with parts of `MathTex` objects (e.g., `tex_object[0][i]`), ensure that the indices are valid and within the bounds of the object's structure. 
    *   Consider generating code that checks the number of `submobjects` or parts before attempting to access them by a specific index, if complex indexing is necessary.
    *   If possible, for `MathTex`, prefer methods like `get_part_by_tex` if you need to reference specific TeX strings, as this can be more robust than numerical indexing.
    *   The goal is to avoid `IndexError` or other runtime issues related to Mobject manipulation.
7.  **Strive for robust code.** If there are multiple ways to achieve an animation, prefer the one that is less prone to common errors.
8.  **IMPORTANT: Generate the complete script.** Do not truncate or leave parts incomplete. The entire animation sequence must be fully implemented.
9.  **Use appropriate wait times** between animations to ensure smooth transitions and readability.
10. **Handle cleanup properly** by removing or fading out objects when they are no longer needed.

Example of expected output structure (this is just a minimal example, your output should be complete based on the user's prompt):
from manim import *
import numpy as np

class {scene_name}(Scene):
    def construct(self):
        # ... Complete Manim code based on the prompt ...
        # For instance, if the prompt asks for a square and then a circle:
        square = Square()
        self.play(Create(square))
        self.wait(1)
        circle = Circle()
        self.play(Transform(square, circle))
        self.wait(1)
        # ... and so on for the entire animation requested.
'''.format(scene_name=scene_name) # scene_name is already part of the system prompt

    user_message_content = f"User's animation prompt: {user_prompt}"

    # --- Anthropic API Call ---
    try:
        from anthropic import Anthropic, APIError

        client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

        # Initialize the model and generate content
        print("Sending prompt to Anthropic Claude model...")
        response = client.messages.create(
            model="claude-3-7-sonnet-latest", # Using Claude 3.7 Sonnet
            max_tokens=16000, # Significantly increased max_tokens for complete script generation
            system=system_prompt,
            messages=[
                {
                    "role": "user",
                    "content": user_message_content
                }
            ]
        )
        
        if response.content and isinstance(response.content, list) and response.content[0].type == "text":
            manim_script_content = response.content[0].text
        else:
            print("Error: Anthropic API response did not contain expected text content.")
            print(f"Full API Response: {response}") # For debugging
            return None
        
        # It's good practice to check the stop reason
        if response.stop_reason not in ["end_turn", "max_tokens"]: # "stop_sequence" is also a valid stop for some models/setups
            print(f"Warning: Anthropic model did not finish generation naturally. Stop Reason: {response.stop_reason}")
            if response.stop_reason == "max_tokens":
                print("Warning: Response was truncated due to token limit. Consider increasing max_tokens or simplifying the prompt.")
                return None

        # Clean up potential Markdown code block delimiters
        content_lines = manim_script_content.strip().splitlines()
        
        if not content_lines:
            manim_script_content = "" # Empty if nothing to process
        else:
            # Check and remove first line if it's a markdown delimiter
            if content_lines[0].strip().startswith("```"):
                content_lines.pop(0)
            
            # Check and remove last line if it's a markdown delimiter
            if content_lines: # Ensure list is not empty after potential pop
                if content_lines[-1].strip() == "```":
                    content_lines.pop(-1)
            
            manim_script_content = "\n".join(content_lines).strip()

    except ImportError:
        print("Error: The 'anthropic' library is not installed. Please install it using 'uv pip install anthropic'.")
        return None
    except APIError as e:
        # Check if the error is due to a missing API key
        if "API key" in str(e).lower():
            print("Error: ANTHROPIC_API_KEY not found or invalid. Please set the ANTHROPIC_API_KEY environment variable.")
        else:
            print(f"Error during Anthropic API call: {e}")
        return None
    except Exception as e:
        print(f"Error during Anthropic API call: {e}")
        # For now, fall back to placeholder if API call fails
        print("Placeholder: Using a dummy Manim script due to Anthropic API call failure.")
        manim_script_content_template = '''
from manim import *
import numpy as np

class {scene_name}(Scene):
    def construct(self):
        # Script generated based on prompt: "{user_prompt}" (Anthropic API Call Failed)
        text = Text("Anthropic API call failed. This is a fallback script.")
        self.play(Write(text))
        self.wait(2)
'''
        manim_script_content = manim_script_content_template.format(scene_name=scene_name, user_prompt=user_prompt)
        return manim_script_content
    # --- End of Anthropic API Call ---

    return manim_script_content


def main():
    parser = argparse.ArgumentParser(description="Generate Manim animations from text prompts.")
    parser.add_argument("--prompt", type=str, required=True, help="Text prompt describing the animation.")
    parser.add_argument("--output_script", type=str, default=DEFAULT_SCRIPT_FILENAME, help="Filename for the generated Manim script.")
    parser.add_argument("--scene_name", type=str, default=DEFAULT_SCENE_NAME, help="Name of the Manim scene in the script.")
    parser.add_argument("--quality", type=str, default=DEFAULT_QUALITY, choices=['l', 'm', 'h', 'k'], help="Rendering quality (l, m, h, k).")
    parser.add_argument("--preview", action="store_true", help="Preview the animation after rendering (opens video).")
    parser.add_argument("--silent", action="store_true", help="Run Manim with less verbose output.")

    args = parser.parse_args()

    print("Generating Manim script using Anthropic Claude...")
    manim_script_content = generate_manim_script_with_anthropic(args.prompt, args.scene_name)

    if not manim_script_content:
        print("Could not generate Manim script from the prompt using Anthropic Claude. Exiting.")
        return

    # print("\nParsed commands:") # No longer applicable with LLM
    # for cmd in parsed_commands:
    #     print(f"- {cmd}")

    # print("\nGenerating Manim code...") # LLM does this directly
    # code_generator = ManimCodeGenerator(scene_name=args.scene_name)
    # manim_script_content = code_generator.generate_code(parsed_commands)

    print("\n--- Generated Manim Script (from Anthropic Claude) ---")
    print(manim_script_content)
    print("--- End of Script ---")

    print("\nRendering animation with Manim...")
    runner = ManimRunner()
    video_file_path = runner.run(
        manim_script_content,
        args.output_script,
        args.scene_name,
        args.quality,
        args.preview,
        args.silent
    )

    if video_file_path:
        print(f"\nProcess complete. Video available at: {video_file_path}")
    else:
        print("\nProcess completed with errors or video path not found.")

if __name__ == "__main__":
    main()
