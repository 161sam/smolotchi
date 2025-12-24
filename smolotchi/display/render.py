from PIL import Image, ImageDraw, ImageFont


def render_state(width: int, height: int, state: str, note: str) -> Image.Image:
    img = Image.new("1", (width, height), 255)
    draw = ImageDraw.Draw(img)

    font_big = ImageFont.load_default()
    font_small = ImageFont.load_default()

    draw.rectangle((0, 0, width, 18), fill=0)
    draw.text((4, 4), "Smolotchi", font=font_small, fill=255)

    draw.text((4, 28), f"STATE: {state}", font=font_big, fill=0)
    if note:
        draw.text((4, 48), note[:32], font=font_small, fill=0)

    draw.text((4, height - 14), "v0.0.1", font=font_small, fill=0)
    return img
