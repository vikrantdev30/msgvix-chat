import os
import shutil
from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen
from PIL import Image, ImageDraw, ImageFont

def bezier_cubic(p0, p1, p2, p3, n=40):
    pts = []
    for i in range(n + 1):
        t = i / n
        u = 1 - t
        x = u**3 * p0[0] + 3 * u**2 * t * p1[0] + 3 * u * t**2 * p2[0] + t**3 * p3[0]
        y = u**3 * p0[1] + 3 * u**2 * t * p1[1] + 3 * u * t**2 * p2[1] + t**3 * p3[1]
        pts.append((x, y))
    return pts

def get_bubble_polygon_points():
    points = []
    points.append((150, 48))
    points.append((362, 48))
    points.extend(bezier_cubic((362, 48), (426, 48), (464, 86), (464, 150))[1:])
    points.append((464, 290))
    points.extend(bezier_cubic((464, 290), (464, 354), (426, 392), (362, 392))[1:])
    points.append((220, 392))
    points.extend(bezier_cubic((220, 392), (160, 392), (116, 430), (96, 456))[1:])
    points.extend(bezier_cubic((96, 456), (88, 466), (78, 458), (86, 442))[1:])
    points.extend(bezier_cubic((86, 442), (98, 420), (102, 392), (48, 310))[1:])
    points.append((48, 150))
    points.extend(bezier_cubic((48, 150), (48, 86), (86, 48), (150, 48))[1:])
    return points

def render_thumbnail(size, scale=4, badge=False):
    target_size = size * scale
    img = Image.new("RGBA", (target_size, target_size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    bubble_pts = get_bubble_polygon_points()
    scaled_bubble = [(x / 512.0 * target_size, y / 512.0 * target_size) for (x, y) in bubble_pts]
    draw.polygon(scaled_bubble, fill="#1F8CEB")

    # Letter M
    stroke_w = int(44 / 512.0 * target_size)
    half_w = stroke_w // 2

    m_pts = [
        (156 / 512.0 * target_size, 310 / 512.0 * target_size),
        (156 / 512.0 * target_size, 150 / 512.0 * target_size),
        (256 / 512.0 * target_size, 248 / 512.0 * target_size),
        (356 / 512.0 * target_size, 150 / 512.0 * target_size),
        (356 / 512.0 * target_size, 310 / 512.0 * target_size)
    ]

    for i in range(len(m_pts) - 1):
        draw.line([m_pts[i], m_pts[i+1]], fill="#FFFFFF", width=stroke_w)
    for p in m_pts:
        draw.ellipse([p[0] - half_w, p[1] - half_w, p[0] + half_w, p[1] + half_w], fill="#FFFFFF")

    # If badge is requested (for unread notifications)
    if badge:
        # Red badge circle in upper right corner with white border
        badge_r = 110 / 512.0 * target_size
        badge_cx = 390 / 512.0 * target_size
        badge_cy = 120 / 512.0 * target_size
        border_w = int(18 / 512.0 * target_size)

        draw.ellipse([
            badge_cx - badge_r - border_w,
            badge_cy - badge_r - border_w,
            badge_cx + badge_r + border_w,
            badge_cy + badge_r + border_w
        ], fill="#FFFFFF")

        draw.ellipse([
            badge_cx - badge_r,
            badge_cy - badge_r,
            badge_cx + badge_r,
            badge_cy + badge_r
        ], fill="#EF4444")

    return img.resize((size, size), Image.Resampling.LANCZOS)

def create_thumbnail_svg(brand_color="#1F8CEB"):
    return f'''<svg width="512" height="512" viewBox="0 0 512 512" fill="none" xmlns="http://www.w3.org/2000/svg">
  <path d="M150 48H362C426 48 464 86 464 150V290C464 354 426 392 362 392H220C160 392 116 430 96 456C88 466 78 458 86 442C98 420 102 392 48 310V150C48 86 86 48 150 48Z" fill="{brand_color}"/>
  <path d="M156 310V150L256 248L356 150V310" stroke="white" stroke-width="44" stroke-linecap="round" stroke-linejoin="round"/>
</svg>
'''

def create_bubble_logo_svg():
    return '''<svg width="66" height="66" viewBox="0 0 66 66" fill="none" xmlns="http://www.w3.org/2000/svg">
  <path d="M19.34 6.19H46.66C54.91 6.19 59.81 11.09 59.81 19.34V37.38C59.81 45.63 54.91 50.53 46.66 50.53H28.36C20.63 50.53 14.95 55.43 12.38 58.78C11.35 60.07 10.06 59.04 11.09 56.98C12.63 54.14 13.15 50.53 6.19 40.09V19.34C6.19 11.09 11.09 6.19 19.34 6.19Z" fill="white"/>
  <path d="M20.1 39.96V19.33L33 31.97L45.9 19.33V39.96" stroke="#1F8CEB" stroke-width="5.67" stroke-linecap="round" stroke-linejoin="round"/>
</svg>
'''

def build_horizontal_logo_svg(dark_mode=False):
    text_color = "#FFFFFF" if dark_mode else "#0F172A"
    brand_color = "#1F8CEB"

    font = TTFont(r'C:\Windows\Fonts\segoeuib.ttf')
    cmap = font.getBestCmap()
    glyph_set = font.getGlyphSet()

    font_scale = 0.0335
    baseline_y = 68
    chars = ['M', 's', 'g', 'v', 'i', 'x']
    paths_svg = []
    current_x = 92.0

    for ch in chars:
        pen = SVGPathPen(glyph_set)
        glyph = glyph_set[cmap[ord(ch)]]
        glyph.draw(pen)
        cmd = pen.getCommands()

        if ch == 'i':
            contours = [c for c in cmd.split('Z') if c.strip()]
            dot_cmd = contours[0] + 'Z'
            stem_cmd = contours[1] + 'Z'
            paths_svg.append(f'<path d="{stem_cmd}" fill="{text_color}" transform="translate({current_x:.2f}, {baseline_y}) scale({font_scale:.5f}, -{font_scale:.5f})" />')
            
            # Chat bubble dot accent
            dot_cx = current_x + 290.0 * font_scale
            dot_cy = baseline_y - 1340.0 * font_scale
            r = 175.0 * font_scale
            paths_svg.append(f'''<g transform="translate({dot_cx:.2f}, {dot_cy:.2f})">
  <path d="M0 -{r:.2f} C{r*1.1:.2f} -{r:.2f} {r*1.1:.2f} {r:.2f} 0 {r:.2f} C-{r*0.6:.2f} {r:.2f} -{r*0.9:.2f} {r*0.7:.2f} -{r:.2f} {r*0.4:.2f} C-{r*1.3:.2f} {r*0.9:.2f} -{r*1.4:.2f} {r*1.1:.2f} -{r*1.5:.2f} {r*1.1:.2f} C-{r*1.4:.2f} {r*0.7:.2f} -{r*1.3:.2f} {r*0.3:.2f} -{r*1.1:.2f} 0 C-{r*1.1:.2f} -{r:.2f} -{r*0.6:.2f} -{r:.2f} 0 -{r:.2f} Z" fill="{brand_color}"/>
</g>''')
        else:
            paths_svg.append(f'<path d="{cmd}" fill="{text_color}" transform="translate({current_x:.2f}, {baseline_y}) scale({font_scale:.5f}, -{font_scale:.5f})" />')

        letter_spacing = -35
        current_x += (glyph.width + letter_spacing) * font_scale

    total_width = int(current_x + 14)
    icon_scale = 68.0 / 512.0
    icon_svg = f'''<g transform="translate(8, 14) scale({icon_scale:.5f})">
  <path d="M150 48H362C426 48 464 86 464 150V290C464 354 426 392 362 392H220C160 392 116 430 96 456C88 466 78 458 86 442C98 420 102 392 48 310V150C48 86 86 48 150 48Z" fill="{brand_color}"/>
  <path d="M156 310V150L256 248L356 150V310" stroke="white" stroke-width="44" stroke-linecap="round" stroke-linejoin="round"/>
</g>'''

    return f'''<svg width="{total_width}" height="96" viewBox="0 0 {total_width} 96" fill="none" xmlns="http://www.w3.org/2000/svg">
  {icon_svg}
  {' '.join(paths_svg)}
</svg>
'''

def render_horizontal_logo_png(dark_mode=False):
    scale = 3
    w = 340 * scale
    h = 96 * scale
    bg_color = (15, 23, 42, 255) if dark_mode else (255, 255, 255, 0)
    text_color = '#FFFFFF' if dark_mode else '#0F172A'
    brand_color = '#1F8CEB'

    img = Image.new('RGBA', (w, h), bg_color)
    draw = ImageDraw.Draw(img)

    # Icon
    icon = render_thumbnail(66 * scale)
    img.paste(icon, (10 * scale, 15 * scale), icon)

    font = ImageFont.truetype(r'C:\Windows\Fonts\segoeuib.ttf', 52 * scale)

    # 'Msgv'
    draw.text((92 * scale, 18 * scale), 'Msgv', font=font, fill=text_color)
    bbox_msgv = font.getbbox('Msgv')
    x_msgv_end = 92 * scale + (bbox_msgv[2] - bbox_msgv[0]) + 1 * scale

    # 'ı'
    draw.text((x_msgv_end, 18 * scale), 'ı', font=font, fill=text_color)
    bbox_i = font.getbbox('ı')
    i_width = bbox_i[2] - bbox_i[0]
    i_center_x = x_msgv_end + i_width / 2.0

    # Chat bubble dot
    dot_r = 6.5 * scale
    dot_cy = 30 * scale
    draw.ellipse([i_center_x - dot_r, dot_cy - dot_r, i_center_x + dot_r, dot_cy + dot_r], fill=brand_color)
    draw.polygon([
        (i_center_x - 3 * scale, dot_cy + 3 * scale),
        (i_center_x - 6 * scale, dot_cy + 8 * scale),
        (i_center_x + 1 * scale, dot_cy + 5 * scale)
    ], fill=brand_color)

    # 'x'
    x_x = x_msgv_end + i_width + 2 * scale
    draw.text((x_x, 18 * scale), 'x', font=font, fill=text_color)

    return img.resize((340, 96), Image.Resampling.LANCZOS)

def create_bot_avatar(size=128):
    # Msgvix bot avatar
    scale = 4
    target = size * scale
    img = Image.new("RGBA", (target, target), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Circle background in #1F8CEB
    draw.ellipse([0, 0, target, target], fill="#1F8CEB")

    # Clean white bot head / M chat mark inside
    # Scaled M chat bubble centered inside
    bubble_icon = render_thumbnail(int(size * 0.72))
    scaled_w, scaled_h = bubble_icon.size
    ox = (size - scaled_w) // 2
    oy = (size - scaled_h) // 2

    # Draw on normal size
    res = img.resize((size, size), Image.Resampling.LANCZOS)
    res.paste(bubble_icon, (ox, oy), bubble_icon)
    return res

def main():
    print("Generating all assets...")
    os.makedirs("brand-assets", exist_ok=True)
    os.makedirs("public/brand-assets", exist_ok=True)

    # 1. SVGs
    thumb_svg = create_thumbnail_svg()
    with open("brand-assets/logo-thumbnail.svg", "w", encoding="utf-8") as f:
        f.write(thumb_svg)
    with open("brand-assets/logo_thumbnail.svg", "w", encoding="utf-8") as f:
        f.write(thumb_svg)
    with open("public/brand-assets/logo_thumbnail.svg", "w", encoding="utf-8") as f:
        f.write(thumb_svg)
    with open("app/javascript/widget/assets/images/logo.svg", "w", encoding="utf-8") as f:
        f.write(thumb_svg)
    if os.path.exists("app/javascript/design-system/images"):
        with open("app/javascript/design-system/images/logo-thumbnail.svg", "w", encoding="utf-8") as f:
            f.write(thumb_svg)

    # Bubble logo
    bubble_svg = create_bubble_logo_svg()
    with open("brand-assets/bubble-logo.svg", "w", encoding="utf-8") as f:
        f.write(bubble_svg)
    with open("app/javascript/dashboard/assets/images/bubble-logo.svg", "w", encoding="utf-8") as f:
        f.write(bubble_svg)

    # Horizontal logo
    logo_svg = build_horizontal_logo_svg(dark_mode=False)
    with open("brand-assets/logo.svg", "w", encoding="utf-8") as f:
        f.write(logo_svg)
    with open("public/brand-assets/logo.svg", "w", encoding="utf-8") as f:
        f.write(logo_svg)

    logo_dark_svg = build_horizontal_logo_svg(dark_mode=True)
    with open("brand-assets/logo_dark.svg", "w", encoding="utf-8") as f:
        f.write(logo_dark_svg)
    with open("public/brand-assets/logo_dark.svg", "w", encoding="utf-8") as f:
        f.write(logo_dark_svg)

    # 2. Raster Horizontal Logos for design-system
    logo_png = render_horizontal_logo_png(dark_mode=False)
    logo_png.save("brand-assets/logo.png")
    if os.path.exists("app/javascript/design-system/images"):
        logo_png.save("app/javascript/design-system/images/logo.png")

    logo_dark_png = render_horizontal_logo_png(dark_mode=True)
    logo_dark_png.save("brand-assets/logo-dark.png")
    if os.path.exists("app/javascript/design-system/images"):
        logo_dark_png.save("app/javascript/design-system/images/logo-dark.png")

    # 3. Favicon and Raster Icons
    thumb_512 = render_thumbnail(512)
    thumb_512.save("brand-assets/favicon.png")
    thumb_512.save("public/favicon.png")
    thumb_512.save("public/favicon-512x512.png")

    # Multi-res favicon.ico
    ico_sizes = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
    thumb_512.save("brand-assets/favicon.ico", format="ICO", sizes=ico_sizes)
    thumb_512.save("public/favicon.ico", format="ICO", sizes=ico_sizes)

    # Standard favicon sizes in public/
    fav_sizes = [16, 32, 96]
    for s in fav_sizes:
        render_thumbnail(s).save(f"public/favicon-{s}x{s}.png")
        # Badge favicons
        render_thumbnail(s, badge=True).save(f"public/favicon-badge-{s}x{s}.png")

    # Android icons
    android_sizes = [36, 48, 72, 96, 144, 192]
    for s in android_sizes:
        render_thumbnail(s).save(f"public/android-icon-{s}x{s}.png")

    # Apple icons
    apple_sizes = [57, 60, 72, 76, 114, 120, 144, 152, 180]
    for s in apple_sizes:
        render_thumbnail(s).save(f"public/apple-icon-{s}x{s}.png")

    apple_180 = render_thumbnail(180)
    apple_192 = render_thumbnail(192)
    apple_192.save("public/apple-icon.png")
    apple_192.save("public/apple-icon-precomposed.png")
    apple_180.save("public/apple-touch-icon.png")
    apple_180.save("public/apple-touch-icon-precomposed.png")

    # MS icons
    render_thumbnail(70).save("public/ms-icon-70x70.png")
    render_thumbnail(144).save("public/ms-icon-144x144.png")
    render_thumbnail(150).save("public/ms-icon-150x150.png")
    render_thumbnail(310).save("public/ms-icon-310x310.png")

    # Bot avatar: 51x51 and 128x128
    bot_avatar = create_bot_avatar(128)
    bot_avatar.save("app/javascript/dashboard/assets/images/chatwoot_bot.png")
    bot_avatar.save("brand-assets/bot_avatar.png")

    print("All assets generated and distributed successfully!")

if __name__ == "__main__":
    main()
