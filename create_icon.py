"""Generate ToDoT application icon - a pixel-art style 'T' with dot pattern."""
import numpy as np

try:
    from PIL import Image, ImageDraw
except ImportError:
    print("Pillow 설치 필요: pip install Pillow")
    raise


def create_icon():
    sizes = [256, 128, 64, 48, 32, 16]
    images = []

    for size in sizes:
        img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        px = max(1, size // 16)

        for y in range(0, size, px):
            for x in range(0, size, px):
                draw.rectangle([x, y, x + px - 1, y + px - 1], fill=(30, 30, 46, 255))

        margin = size // 8
        inner = size - margin * 2

        for y in range(margin, margin + px * 3, px):
            for x in range(margin, margin + inner, px):
                draw.rectangle([x, y, x + px - 1, y + px - 1], fill=(137, 180, 250, 255))

        t_col_start = margin + (inner // 2) - px
        t_col_end = t_col_start + px * 3
        for y in range(margin + px * 3, margin + inner, px):
            for x in range(t_col_start, t_col_end, px):
                draw.rectangle([x, y, x + px - 1, y + px - 1], fill=(137, 180, 250, 255))

        dot_positions = [
            (margin + px, margin + inner - px * 2),
            (margin + inner - px * 2, margin + inner - px * 2),
            (margin + px, margin + inner // 2),
            (margin + inner - px * 2, margin + inner // 2),
        ]
        for dx, dy in dot_positions:
            draw.rectangle([dx, dy, dx + px - 1, dy + px - 1], fill=(250, 179, 135, 255))

        images.append(img)

    images[0].save("icon.ico", format="ICO", sizes=[(s, s) for s in sizes],
                    append_images=images[1:])
    images[0].save("icon.png", format="PNG")
    print("icon.ico, icon.png 생성 완료!")


if __name__ == "__main__":
    create_icon()
