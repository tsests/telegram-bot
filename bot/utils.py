import re
from PIL import Image, ImageDraw, ImageFont
import pyfiglet
import base64
import io

def get_multiline_text_size(ascii_art, font):
    d = ImageDraw.Draw(Image.new("RGB", (1, 1)))
    lines = ascii_art.split("\n")
    max_width = 0
    total_height = 0

    for line in lines:
        line_width = d.textlength(line, font=font)
        max_width = max(max_width, line_width)
        total_height += font.getsize(line)[1]

    return max_width, total_height

def escape_markdown(text: str) -> str:
    escape_chars = r'\_*[]()~`>#+-=|{}.!'
    return ''.join(['\\' + c if c in escape_chars else c for c in text])

def generate_ascii_art(text: str) -> str:
    return pyfiglet.figlet_format(text)

def encode_hidden_text(hidden_text: str) -> bytes:
    return base64.b64encode(hidden_text.encode("utf-8"))

