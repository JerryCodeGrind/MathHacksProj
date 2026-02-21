# sheets.py
import pygame

def _parse_atlas(atlas_path: str) -> dict[str, pygame.Rect]:
    """
    Parses your cars.atlas file (Spine/TexturePacker style).
    Returns: {name: pygame.Rect(x, y, w, h)} based on xy/size.
    Assumes rotate: false (your atlas shows rotate: false).
    """
    rects: dict[str, pygame.Rect] = {}

    with open(atlas_path, "r", encoding="utf-8") as f:
        lines = [ln.rstrip("\n") for ln in f]

    name = None
    xy = None
    size = None

    def flush():
        nonlocal name, xy, size
        if name and xy and size:
            x, y = xy
            w, h = size
            rects[name] = pygame.Rect(x, y, w, h)
        name = None
        xy = None
        size = None

    for raw in lines:
        line = raw.strip()
        if not line:
            continue

        # skip top header lines like:
        # cars.png / format: / filter: / repeat:
        if line.endswith(".png") or line.startswith(("format:", "filter:", "repeat:")):
            continue

        # region name line: has no ':'
        if ":" not in line:
            flush()
            name = line
            continue

        if name is None:
            continue

        if line.startswith("xy:"):
            v = line.split(":", 1)[1].strip()
            a, b = [p.strip() for p in v.split(",")]
            xy = (int(a), int(b))

        elif line.startswith("size:"):
            v = line.split(":", 1)[1].strip()
            a, b = [p.strip() for p in v.split(",")]
            size = (int(a), int(b))

        # rotate/orig/offset/index not needed for cropping

    flush()

    if not rects:
        raise ValueError(f"No regions parsed from atlas: {atlas_path}")

    return rects


# Load once at import time
_ATLAS_RECTS = _parse_atlas("cars.atlas")
ATLAS_KEYS = list(_ATLAS_RECTS.keys())


class SpriteSheet:
    def __init__(self, png_path: str):
        self.sheet = pygame.image.load(png_path).convert_alpha()

    def get_scaled(self, name: str, size: tuple[int, int]) -> pygame.Surface:
        rect = _ATLAS_RECTS[name]
        img = self.sheet.subsurface(rect).copy()
        return pygame.transform.scale(img, size)