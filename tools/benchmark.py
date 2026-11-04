"""Measure drawing work without networking, display updates, or the frame cap."""

import argparse
import json
import os
from pathlib import Path
import statistics
import sys
import time
from types import SimpleNamespace

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pygame
from main import App
from scripts.game_instance import GameInstance


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--frames", type=int, default=1000)
    parser.add_argument("--preview", type=Path)
    args = parser.parse_args()
    if args.frames < 1:
        parser.error("--frames must be positive")
    app = App()
    try:
        game = GameInstance(0)
        for _ in range(4):
            game.add_player()
        game.food = (15, 15)
        app.game_instance = SimpleNamespace(**game.snapshot())
        app.vrt_space.update()
        for _ in range(30):
            app.renderer.render()
        times = []
        for _ in range(args.frames):
            start = time.perf_counter()
            app.vrt_space.update()
            app.renderer.render()
            times.append((time.perf_counter() - start) * 1000)
        if args.preview:
            args.preview.parent.mkdir(parents=True, exist_ok=True)
            pygame.image.save(app.window.app_window, str(args.preview))
        print(json.dumps({"players": 4, "frames": args.frames,
                          "median_ms": round(statistics.median(times), 3)}, indent=2))
    finally:
        app.close()


if __name__ == "__main__":
    main()
