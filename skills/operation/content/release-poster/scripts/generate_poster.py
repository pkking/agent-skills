#!/usr/bin/env python3
"""
Release Poster Generator

Generate professional tech-style release announcement posters.
Supports mixed Chinese/English text with categorized update icons.
"""

from PIL import Image, ImageDraw, ImageFont, ImageFilter
import math
import os

# ============ Configuration ============
WIDTH = 750
HEIGHT = 1050

# Colors
TITLE_BLUE = (30, 64, 175)
TEXT_DARK = (51, 65, 85)
TEXT_GRAY = (100, 116, 139)
WHITE = (255, 255, 255)
DIVIDER_COLOR = (226, 232, 240)

# Font paths (adjust for your system)
CN_FONT_PATH = '/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf'
EN_FONT_PATH = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
EN_BOLD_PATH = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'


def is_chinese(char):
    """Check if character is Chinese."""
    return '\u4e00' <= char <= '\u9fff' or char in '，。！？、：；""''（）【】'


def draw_mixed_text(draw, x, y, text, cn_font, en_font, color, anchor=None):
    """Draw mixed Chinese/English text."""
    current_x = x
    if anchor and 'm' in anchor:
        total_width = sum(
            draw.textbbox((0, 0), char, font=cn_font if is_chinese(char) else en_font)[2]
            for char in text
        )
        current_x = x - total_width // 2

    for char in text:
        font = cn_font if is_chinese(char) else en_font
        draw.text((current_x, y), char, fill=color, font=font)
        bbox = draw.textbbox((0, 0), char, font=font)
        current_x += bbox[2] - bbox[0]
    return current_x - x


def draw_mixed_text_wrap(draw, x, y, text, cn_font, en_font, color, max_width):
    """Draw mixed text with word wrapping."""
    lines, current_line, current_width = [], "", 0

    for char in text:
        font = cn_font if is_chinese(char) else en_font
        char_width = draw.textbbox((0, 0), char, font=font)[2]

        if current_width + char_width <= max_width:
            current_line += char
            current_width += char_width
        else:
            lines.append(current_line)
            current_line, current_width = char, char_width

    if current_line:
        lines.append(current_line)

    line_height = 28
    for i, line in enumerate(lines):
        draw_mixed_text(draw, x, y + i * line_height, line, cn_font, en_font, color)
    return len(lines) * line_height


def draw_icon(draw, x, y, icon_type, size=20):
    """Draw categorized icon."""
    if icon_type == "star":
        points = []
        for i in range(5):
            outer = math.radians(90 + i * 72)
            inner = math.radians(90 + i * 72 + 36)
            points.append((x + size//2 + int(size//2 * math.cos(outer)),
                          y + size//2 - int(size//2 * math.sin(outer))))
            points.append((x + size//2 + int(size//4 * math.cos(inner)),
                          y + size//2 - int(size//4 * math.sin(inner))))
        draw.polygon(points, fill=(250, 204, 21))
    elif icon_type == "party":
        draw.ellipse([(x, y), (x+size, y+size)], fill=(250, 204, 21), outline=(234, 179, 8), width=2)
    elif icon_type == "rocket":
        draw.ellipse([(x, y), (x+size, y+size)], fill=(239, 68, 68))
        draw.polygon([(x+size//2, y+3), (x+size-4, y+size-3), (x+4, y+size-3)], fill=WHITE)
    elif icon_type == "fire":
        draw.ellipse([(x, y), (x+size, y+size)], fill=(249, 115, 22))
    elif icon_type == "bug":
        draw.ellipse([(x, y), (x+size, y+size)], fill=(239, 68, 68))
        draw.ellipse([(x+4, y+4), (x+size-4, y+size-4)], fill=(127, 29, 29))
    elif icon_type == "refresh":
        draw.ellipse([(x, y), (x+size, y+size)], fill=(59, 130, 246))
        draw.arc([(x+3, y+3), (x+size-3, y+size-3)], 30, 300, fill=WHITE, width=2)
    elif icon_type == "warning":
        draw.polygon([(x+size//2, y), (x+size, y+size), (x, y+size)],
                    fill=(250, 204, 21), outline=(234, 179, 8))


def draw_tech_decorations(img, draw):
    """Draw tech-style background decorations."""
    # Top-right gradient glow
    glow = Image.new('RGBA', (WIDTH, HEIGHT), (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(glow)
    for r in range(250, 0, -3):
        alpha = int(18 * (1 - r/250))
        glow_draw.ellipse([(WIDTH - 100 - r, -150 - r), (WIDTH - 100 + r, -150 + r)],
                          fill=(99, 155, 255, alpha))
    img = Image.alpha_composite(img, glow)

    # Bottom-left gradient glow
    glow2 = Image.new('RGBA', (WIDTH, HEIGHT), (0, 0, 0, 0))
    glow_draw2 = ImageDraw.Draw(glow2)
    for r in range(200, 0, -3):
        alpha = int(15 * (1 - r/200))
        glow_draw2.ellipse([(-120 - r, HEIGHT - 100 - r), (-120 + r, HEIGHT - 100 + r)],
                           fill=(120, 200, 180, alpha))
    img = Image.alpha_composite(img, glow2)
    draw = ImageDraw.Draw(img)

    # Decorative circles (top-right)
    draw.ellipse([(WIDTH - 100, 30), (WIDTH - 55, 75)], outline=(200, 215, 240), width=2)
    draw.ellipse([(WIDTH - 50, 70), (WIDTH - 30, 90)], outline=(200, 215, 240), width=1)
    draw.ellipse([(WIDTH - 75, 85), (WIDTH - 68, 92)], fill=(200, 215, 240))
    draw.ellipse([(WIDTH - 40, 50), (WIDTH - 35, 55)], fill=(200, 215, 240))

    # Decorative circles (bottom-left)
    draw.ellipse([(25, HEIGHT - 100), (70, HEIGHT - 55)], outline=(200, 220, 235), width=2)
    draw.ellipse([(75, HEIGHT - 70), (92, HEIGHT - 53)], outline=(200, 220, 235), width=1)
    draw.ellipse([(50, HEIGHT - 50), (56, HEIGHT - 44)], fill=(200, 220, 235))

    # Right side accent lines
    for i in range(3):
        y_start = 280 + i * 100
        draw.line([(WIDTH - 22, y_start), (WIDTH - 22, y_start + 50)], fill=(210, 220, 240), width=2)
        draw.ellipse([(WIDTH - 26, y_start + 50), (WIDTH - 18, y_start + 58)], fill=(210, 220, 240))

    # Left side accent lines
    for i in range(2):
        y_start = 350 + i * 120
        draw.line([(18, y_start), (18, y_start + 40)], fill=(210, 225, 240), width=2)
        draw.ellipse([(14, y_start - 6), (22, y_start + 2)], fill=(210, 225, 240))

    return img, draw


def create_release_poster(
    title: str,
    version: str,
    items: list,
    footer_text: str = "",
    output_path: str = "release-poster.png",
    section_title: str = "亮点更新",
    width: int = WIDTH,
    height: int = HEIGHT
):
    """
    Generate a release announcement poster.

    Args:
        title: Project name (e.g., "vLLM Ascend")
        version: Version string (e.g., "v0.11.0")
        items: List of (icon_type, text) tuples
        footer_text: Optional footer text (e.g., GitHub link)
        output_path: Output file path
        section_title: Section header text
        width: Image width
        height: Image height
    """
    global WIDTH, HEIGHT
    WIDTH, HEIGHT = width, height

    # Create gradient background
    img = Image.new('RGBA', (WIDTH, HEIGHT), (255, 255, 255))
    draw = ImageDraw.Draw(img)

    for y in range(HEIGHT):
        ratio = y / HEIGHT
        r = int(235 + (255 - 235) * ratio)
        g = int(245 + (255 - 245) * ratio)
        b = 255
        draw.line([(0, y), (WIDTH, y)], fill=(r, g, b))

    # Add tech decorations
    img, draw = draw_tech_decorations(img, draw)

    # Load fonts
    cn_title = ImageFont.truetype(CN_FONT_PATH, 50)
    cn_section = ImageFont.truetype(CN_FONT_PATH, 26)
    cn_text = ImageFont.truetype(CN_FONT_PATH, 19)
    cn_small = ImageFont.truetype(CN_FONT_PATH, 14)
    en_title = ImageFont.truetype(EN_BOLD_PATH, 50)
    en_section = ImageFont.truetype(EN_FONT_PATH, 26)
    en_text = ImageFont.truetype(EN_FONT_PATH, 19)
    en_small = ImageFont.truetype(EN_FONT_PATH, 14)

    # Draw title
    title_y = 50
    draw_mixed_text(draw, WIDTH//2, title_y, title, cn_title, en_title, TITLE_BLUE, anchor="mt")
    draw_mixed_text(draw, WIDTH//2, title_y + 58, f"{version} 发布", cn_title, en_title, TITLE_BLUE, anchor="mt")

    # White card with shadow
    card_top, card_left = 175, 40
    card_right, card_bottom = WIDTH - 40, HEIGHT - 45
    card_radius = 20

    shadow = Image.new('RGBA', (WIDTH, HEIGHT), (0, 0, 0, 0))
    shadow_draw = ImageDraw.Draw(shadow)
    shadow_draw.rounded_rectangle(
        [(card_left + 4, card_top + 4), (card_right + 4, card_bottom + 4)],
        radius=card_radius, fill=(100, 120, 150, 25)
    )
    shadow = shadow.filter(ImageFilter.GaussianBlur(radius=8))
    img = Image.alpha_composite(img, shadow)

    card = Image.new('RGBA', (WIDTH, HEIGHT), (0, 0, 0, 0))
    card_draw = ImageDraw.Draw(card)
    card_draw.rounded_rectangle(
        [(card_left, card_top), (card_right, card_bottom)],
        radius=card_radius, fill=(255, 255, 255, 252)
    )
    img = Image.alpha_composite(img, card)
    draw = ImageDraw.Draw(img)

    # Content
    y_pos = card_top + 28
    x_left = card_left + 30
    content_width = card_right - x_left - 45

    # Section header
    draw_icon(draw, x_left, y_pos, "star", 24)
    draw_mixed_text(draw, x_left + 32, y_pos - 2, section_title, cn_section, en_section, TEXT_DARK)
    y_pos += 45

    # Items
    for icon_type, text in items:
        if icon_type == "divider":
            y_pos += 8
            draw.line([(x_left, y_pos), (card_right - 35, y_pos)], fill=DIVIDER_COLOR, width=1)
            y_pos += 18
        else:
            draw_icon(draw, x_left, y_pos + 2, icon_type, 20)
            height = draw_mixed_text_wrap(draw, x_left + 32, y_pos, text, cn_text, en_text, TEXT_DARK, content_width)
            y_pos += max(height, 28) + 8

    # Footer
    if footer_text:
        footer_y = card_bottom + 15
        draw_mixed_text(draw, WIDTH//2, footer_y, footer_text, cn_small, en_small, TEXT_GRAY, anchor="mt")

    # Save
    img.convert('RGB').save(output_path, 'PNG', quality=95)
    print(f"Poster saved to: {output_path}")
    return output_path


if __name__ == "__main__":
    # Example usage
    items = [
        ("party", "本版本共计6个commits，新增1位新开发者！"),
        ("rocket", "DeepSeek 3/3.1 系列性能显著提升，满足高性能推理场景诉求"),
        ("rocket", "采样操作性能优化，提升整体推理效率"),
        ("rocket", "Kimi-K2 模型性能优化，改善用户体验"),
        ("fire", "Eagle3 推测解码功能恢复支持"),
        ("bug", "修复 Qwen3-VL 精度问题，提升多模态推理准确性"),
        ("bug", "修复 DeepSeek3.2-exp 量化bug"),
        ("bug", "修复 Qwen3-VL-MOE 高并发场景稳定性问题"),
        ("bug", "修复 Prefill-Decode 分离场景精度问题"),
        ("bug", "修复 EPLB 相关bug，增强负载均衡稳定性"),
        ("bug", "修复 openEuler Docker镜像版本兼容性问题"),
        ("divider", ""),
        ("refresh", "torch-npu 升级至 2.7.1.post1"),
        ("refresh", "CANN 升级至 8.3.rc2"),
        ("divider", ""),
        ("warning", "废弃预告：LLMdatadist connector、Torchair graph、Ascend scheduler 将在 v0.12.0rc1 移除"),
    ]

    create_release_poster(
        title="vLLM Ascend",
        version="v0.11.0",
        items=items,
        footer_text="GitHub: github.com/vllm-project/vllm-ascend",
        output_path="example-release-poster.png"
    )
