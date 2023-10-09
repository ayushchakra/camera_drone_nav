from gtts import gTTS
from pathlib import Path
from slugify import slugify

def main():
    movement_commands_by_file_name = {
        "left": "move left",
        "right": "move right",
        "up": "move up",
        "down": "move down",
        "forward": "move forward",
        "backward": "move backward",
        "none": "no april tag, move around",
        "reached": "reached destination",
        "success": "navigation complete"
    }
    for filename, command_text in movement_commands_by_file_name.items():
        tts = gTTS(text=command_text, lang="en", slow=False)
        tts.save(f"{Path(__file__).parent}/{filename}.mp3")

if __name__ == "__main__":
    main()