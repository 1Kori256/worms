from functools import lru_cache
import json
from pathlib import Path


def load_config(path):
    config = {}
    for file in sorted(Path(path).glob("*_config.json")):
        with file.open(encoding="utf-8") as source:
            config[file.name[:-12]] = json.load(source)
    return config


@lru_cache(maxsize=128)
def debug_text(font, text):
    return font.render(text, True, (240, 240, 240))


def debug(surface, font, pos, *args):
    for i, arg in enumerate(args):
        surface.blit(debug_text(font, str(arg)), (pos[0], pos[1] + i * 16))
