"""
Generate an ultra-modern, AAA-grade application icon for Nexus File Manager.
Inspired by modern icons like Brave, Steam, and Raycast:
- 4x Supersampled (1024x1024 downsampled via Lanczos to 256, 128, 64, 48, 32, 16)
- Dimensional metallic squircle base with chamfered rim lighting and dark carbon-glass gradient
- Faceted 3D Geometric Nexus Core with multi-tone neon-cyan / royal-violet gradients
- Physical surface bevels, specular lighting reflections, and ambient depth drop-shadows
"""

from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter
import math

ROOT_DIR = Path(__file__).resolve().parent
ASSETS_DIR = ROOT_DIR / "assets"
ASSETS_DIR.mkdir(parents=True, exist_ok=True)
PNG_PATH = ASSETS_DIR / "icon.png"
ICO_PATH = ASSETS_DIR / "icon.ico"


def lerp_color(c1, c2, t):
    return tuple(int(a + (b - a) * t) for a, b in zip(c1, c2))


def draw_linear_gradient(draw, x0, y0, x1, y1, c1, c2, mask=None):
    # Quick vertical gradient fill into a polygon/mask
    pass


def create_nexus_icon():
    CANVAS_SIZE = 1024  # 4x supersampling
    scale = CANVAS_SIZE / 256.0

    img = Image.new("RGBA", (CANVAS_SIZE, CANVAS_SIZE), (0, 0, 0, 0))

    # 1. Base Shadow Layer (soft diffused ambient drop shadow)
    shadow = Image.new("RGBA", (CANVAS_SIZE, CANVAS_SIZE), (0, 0, 0, 0))
    s_draw = ImageDraw.Draw(shadow)
    margin = int(22 * scale)
    pad_b = int(32 * scale)
    s_draw.rounded_rectangle(
        [margin, margin + int(12 * scale), CANVAS_SIZE - margin, CANVAS_SIZE - margin + int(14 * scale)],
        radius=int(56 * scale),
        fill=(0, 0, 0, 160)
    )
    shadow = shadow.filter(ImageFilter.GaussianBlur(radius=int(18 * scale)))
    img = Image.alpha_composite(img, shadow)

    # 2. Main Squircle Base (Dark Obsidian Glass / Titanium)
    base = Image.new("RGBA", (CANVAS_SIZE, CANVAS_SIZE), (0, 0, 0, 0))
    b_draw = ImageDraw.Draw(base)
    box = [margin, margin, CANVAS_SIZE - margin, CANVAS_SIZE - margin]
    rad = int(58 * scale)

    # Create smooth vertical gradient on the base squircle
    base_mask = Image.new("L", (CANVAS_SIZE, CANVAS_SIZE), 0)
    m_draw = ImageDraw.Draw(base_mask)
    m_draw.rounded_rectangle(box, radius=rad, fill=255)

    base_grad = Image.new("RGBA", (CANVAS_SIZE, CANVAS_SIZE), (0, 0, 0, 0))
    bg_draw = ImageDraw.Draw(base_grad)
    for y in range(CANVAS_SIZE):
        t = y / CANVAS_SIZE
        # Top: Deep Slate Navy (#131B2E), Bottom: Dark Obsidian (#070B14)
        r = int(19 * (1 - t) + 7 * t)
        g = int(27 * (1 - t) + 11 * t)
        b = int(46 * (1 - t) + 20 * t)
        bg_draw.line([(0, y), (CANVAS_SIZE, y)], fill=(r, g, b, 255))
    base = Image.composite(base_grad, base, base_mask)

    # 3. Outer Rim Chamfer & Specular Edge Lighting
    rim = Image.new("RGBA", (CANVAS_SIZE, CANVAS_SIZE), (0, 0, 0, 0))
    r_draw = ImageDraw.Draw(rim)
    # Beveled border: 4px stroke
    b_stroke = int(4.5 * scale)
    for i in range(b_stroke):
        inset = margin + i
        t_alpha = int(140 - (i * 25))
        r_draw.rounded_rectangle(
            [inset, inset, CANVAS_SIZE - inset, CANVAS_SIZE - inset],
            radius=rad - i,
            outline=(56, 189, 248, max(20, t_alpha)),
            width=1
        )
    # Top rim specular highlight (glowing light source from top-left)
    for x in range(margin + rad, CANVAS_SIZE - margin - rad):
        ratio = (x - (margin + rad)) / (CANVAS_SIZE - 2 * (margin + rad))
        intensity = math.sin(ratio * math.pi)
        alpha = int(180 * intensity)
        r_draw.point((x, margin), fill=(255, 255, 255, alpha))
        r_draw.point((x, margin + 1), fill=(56, 189, 248, int(alpha * 0.8)))

    base = Image.alpha_composite(base, rim)
    img = Image.alpha_composite(img, base)

    # 4. Central Glowing Radial Aura behind the Nexus Logo
    glow = Image.new("RGBA", (CANVAS_SIZE, CANVAS_SIZE), (0, 0, 0, 0))
    g_draw = ImageDraw.Draw(glow)
    cx, cy = CANVAS_SIZE // 2, CANVAS_SIZE // 2 - int(4 * scale)
    glow_r = int(190 * scale)
    for r in range(glow_r, 0, -3):
        frac = 1.0 - (r / glow_r)
        a = int((frac ** 2.2) * 90)
        # Electric Violet/Cyan aura
        cr = int(14 + 110 * frac)
        cg = int(165 + 40 * frac)
        cb = int(240 + 15 * frac)
        g_draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(cr, cg, cb, a))
    img = Image.alpha_composite(img, glow)

    # 5. The Faceted 3D "NEXUS" Origami Core (Geometric Prism Emblem)
    # The emblem consists of precision polygonal facets with lighting vectors:
    # - Left Wing (Electric Cyan facet + Cyan shadow facet)
    # - Central Fold (Radiant Violet & Magenta diagonal bridge)
    # - Right Wing (Deep Sapphire / Neon Azure facet + Top bevel)
    # - Center Nexus Diamond Spark
    emblem = Image.new("RGBA", (CANVAS_SIZE, CANVAS_SIZE), (0, 0, 0, 0))
    e_draw = ImageDraw.Draw(emblem)

    # Center coordinates & proportional dimensions
    w_half = int(58 * scale)
    h_half = int(68 * scale)
    thickness = int(22 * scale)

    # Key anchor points for the 3D Nexus Ribbon
    # Left Column
    P_TL = (cx - w_half, cy - h_half)
    P_TR1 = (cx - w_half + thickness, cy - h_half + int(12 * scale))
    P_BL = (cx - w_half, cy + h_half)
    P_BR1 = (cx - w_half + thickness, cy + h_half)

    # Right Column
    P_TR2 = (cx + w_half, cy - h_half)
    P_TL2 = (cx + w_half - thickness, cy - h_half)
    P_BR2 = (cx + w_half, cy + h_half)
    P_BL2 = (cx + w_half - thickness, cy + h_half - int(12 * scale))

    # Central Nexus nodes
    P_C1 = (cx, cy - int(14 * scale))
    P_C2 = (cx, cy + int(14 * scale))

    # Facet 1: Left Wing Outer Surface (Vibrant Cyan-Blue Gradient)
    poly_left_outer = [P_TL, (cx - w_half + thickness, cy - h_half), P_BR1, P_BL]
    # Draw left facet with vertical shading
    facet1 = Image.new("RGBA", (CANVAS_SIZE, CANVAS_SIZE), (0, 0, 0, 0))
    f1_draw = ImageDraw.Draw(facet1)
    f1_draw.polygon(poly_left_outer, fill=(0, 210, 255, 255))
    # Bevel shading
    f1_shade = Image.new("RGBA", (CANVAS_SIZE, CANVAS_SIZE), (0, 0, 0, 0))
    f1s_draw = ImageDraw.Draw(f1_shade)
    for y in range(int(P_TL[1]), int(P_BL[1])):
        t = (y - P_TL[1]) / (P_BL[1] - P_TL[1] + 1)
        r = int(56 * (1 - t) + 14 * t)
        g = int(215 * (1 - t) + 140 * t)
        b = int(255 * (1 - t) + 240 * t)
        f1s_draw.line([(0, y), (CANVAS_SIZE, y)], fill=(r, g, b, 255))
    mask1 = Image.new("L", (CANVAS_SIZE, CANVAS_SIZE), 0)
    ImageDraw.Draw(mask1).polygon(poly_left_outer, fill=255)
    facet1 = Image.composite(f1_shade, facet1, mask1)
    emblem = Image.alpha_composite(emblem, facet1)

    # Facet 2: Left Wing Inner Reflected Edge
    poly_left_inner = [(cx - w_half + thickness, cy - h_half), P_C1, (cx - w_half + thickness, cy + int(10 * scale)), P_BR1]
    mask2 = Image.new("L", (CANVAS_SIZE, CANVAS_SIZE), 0)
    ImageDraw.Draw(mask2).polygon(poly_left_inner, fill=255)
    f2_grad = Image.new("RGBA", (CANVAS_SIZE, CANVAS_SIZE), (0, 0, 0, 0))
    f2_draw = ImageDraw.Draw(f2_grad)
    for y in range(CANVAS_SIZE):
        t = y / CANVAS_SIZE
        f2_draw.line([(0, y), (CANVAS_SIZE, y)], fill=(12, 140, 210, 255))
    emblem = Image.composite(f2_grad, emblem, mask2)

    # Facet 3: Dynamic Central Diagonal Ribbon (Neon Violet to Magenta Flame)
    poly_diag = [P_TL, (cx - int(10 * scale), cy - h_half + int(18 * scale)), P_BR2, (cx + int(10 * scale), cy + h_half - int(18 * scale))]
    mask3 = Image.new("L", (CANVAS_SIZE, CANVAS_SIZE), 0)
    ImageDraw.Draw(mask3).polygon(poly_diag, fill=255)
    f3_grad = Image.new("RGBA", (CANVAS_SIZE, CANVAS_SIZE), (0, 0, 0, 0))
    f3_draw = ImageDraw.Draw(f3_grad)
    for y in range(CANVAS_SIZE):
        t = y / CANVAS_SIZE
        # Magenta-Violet gradient: #E024C3 -> #6366F1
        r = int(230 * (1 - t) + 99 * t)
        g = int(45 * (1 - t) + 102 * t)
        b = int(210 * (1 - t) + 241 * t)
        f3_draw.line([(0, y), (CANVAS_SIZE, y)], fill=(r, g, b, 255))
    emblem = Image.composite(f3_grad, emblem, mask3)

    # Facet 4: Right Wing Outer Surface (Electric Azure / Cobalt)
    poly_right_outer = [P_TL2, P_TR2, P_BR2, P_BL2]
    mask4 = Image.new("L", (CANVAS_SIZE, CANVAS_SIZE), 0)
    ImageDraw.Draw(mask4).polygon(poly_right_outer, fill=255)
    f4_grad = Image.new("RGBA", (CANVAS_SIZE, CANVAS_SIZE), (0, 0, 0, 0))
    f4_draw = ImageDraw.Draw(f4_grad)
    for y in range(int(P_TR2[1]), int(P_BR2[1])):
        t = (y - P_TR2[1]) / (P_BR2[1] - P_TR2[1] + 1)
        r = int(99 * (1 - t) + 30 * t)
        g = int(102 * (1 - t) + 64 * t)
        b = int(241 * (1 - t) + 175 * t)
        f4_draw.line([(0, y), (CANVAS_SIZE, y)], fill=(r, g, b, 255))
    emblem = Image.composite(f4_grad, emblem, mask4)

    # Facet 5: Top Specular Crystal Caps (Diamond Bevels)
    cap_left = [P_TL, (cx - w_half + int(14 * scale), cy - h_half - int(8 * scale)), (cx - w_half + thickness + int(14 * scale), cy - h_half - int(8 * scale)), (cx - w_half + thickness, cy - h_half)]
    cap_right = [P_TL2, (cx + w_half - thickness + int(14 * scale), cy - h_half - int(8 * scale)), (cx + w_half + int(14 * scale), cy - h_half - int(8 * scale)), P_TR2]
    e_draw.polygon(cap_left, fill=(200, 245, 255, 230))
    e_draw.polygon(cap_right, fill=(230, 215, 255, 230))

    # 6. Central Nexus Core Spark (Luminous 4-point Diamond Star)
    star_cx, star_cy = cx, cy
    star_w = int(20 * scale)
    star_h = int(26 * scale)
    star_poly = [
        (star_cx, star_cy - star_h),
        (star_cx + int(star_w * 0.4), star_cy - int(star_h * 0.2)),
        (star_cx + star_w, star_cy),
        (star_cx + int(star_w * 0.4), star_cy + int(star_h * 0.2)),
        (star_cx, star_cy + star_h),
        (star_cx - int(star_w * 0.4), star_cy + int(star_h * 0.2)),
        (star_cx - star_w, star_cy),
        (star_cx - int(star_w * 0.4), star_cy - int(star_h * 0.2)),
    ]
    star_glow = Image.new("RGBA", (CANVAS_SIZE, CANVAS_SIZE), (0, 0, 0, 0))
    sg_draw = ImageDraw.Draw(star_glow)
    sg_draw.polygon(star_poly, fill=(255, 255, 255, 255))
    sg_draw.ellipse([star_cx - int(24 * scale), star_cy - int(24 * scale), star_cx + int(24 * scale), star_cy + int(24 * scale)], fill=(56, 189, 248, 120))
    star_glow = star_glow.filter(ImageFilter.GaussianBlur(radius=int(4 * scale)))
    emblem = Image.alpha_composite(emblem, star_glow)
    e_draw.polygon(star_poly, fill=(255, 255, 255, 255))

    # Add emblem drop shadow onto the base
    emblem_shadow = Image.new("RGBA", (CANVAS_SIZE, CANVAS_SIZE), (0, 0, 0, 0))
    es_draw = ImageDraw.Draw(emblem_shadow)
    # Re-draw combined silhouette offset
    off_y = int(14 * scale)
    for p in [poly_left_outer, poly_diag, poly_right_outer]:
        off_poly = [(x, y + off_y) for x, y in p]
        es_draw.polygon(off_poly, fill=(0, 0, 0, 140))
    emblem_shadow = emblem_shadow.filter(ImageFilter.GaussianBlur(radius=int(12 * scale)))
    img = Image.alpha_composite(img, emblem_shadow)
    img = Image.alpha_composite(img, emblem)

    # 7. Final Downsampling via high-precision Lanczos Filter for Razor-Sharpness
    final_256 = img.resize((256, 256), Image.Resampling.LANCZOS)
    final_256.save(PNG_PATH, "PNG")

    # Generate multi-resolution Windows ICO (256, 128, 64, 48, 32, 16)
    sizes = [(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)]
    ico_images = [img.resize(s, Image.Resampling.LANCZOS) for s in sizes]
    ico_images[0].save(ICO_PATH, format="ICO", sizes=sizes, append_images=ico_images[1:])

    print(f"High-quality AAA application icon generated at: {PNG_PATH} and {ICO_PATH}")


if __name__ == "__main__":
    create_nexus_icon()
