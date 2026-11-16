"""Generate high-resolution application icons for Nexus File Manager."""

from pathlib import Path
from PIL import Image, ImageDraw

ASSETS_DIR = Path(__file__).resolve().parent / "assets"
ASSETS_DIR.mkdir(parents=True, exist_ok=True)
PNG_PATH = ASSETS_DIR / "icon.png"
ICO_PATH = ASSETS_DIR / "icon.ico"


def create_app_icon():
    # 256x256 high-res icon
    size = (256, 256)
    img = Image.new("RGBA", size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Outer rounded shield / square
    draw.rounded_rectangle([12, 12, 244, 244], radius=48, fill="#0B0F19", outline="#38BDF8", width=6)

    # Folder shape
    # Folder tab
    draw.rounded_rectangle([45, 55, 125, 95], radius=12, fill="#1E293B", outline="#38BDF8", width=4)
    # Folder body
    draw.rounded_rectangle([45, 80, 211, 200], radius=18, fill="#1E293B", outline="#38BDF8", width=4)

    # Glowing inner accent (Nexus Spark / Diamond)
    diamond = [(128, 105), (160, 140), (128, 175), (96, 140)]
    draw.polygon(diamond, fill="#38BDF8", outline="#818CF8")

    # Inner bright dot
    draw.ellipse([120, 132, 136, 148], fill="#FFFFFF")

    img.save(PNG_PATH, "PNG")
    # Save as multi-size ICO
    img.save(ICO_PATH, format="ICO", sizes=[(256, 256), (64, 64), (48, 48), (32, 32), (16, 16)])
    print(f"Icons generated at: {PNG_PATH} and {ICO_PATH}")


if __name__ == "__main__":
    create_app_icon()
