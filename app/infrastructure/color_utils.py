def darken_hex(hex_color: str, factor: float = 0.75) -> str:
    h = hex_color.lstrip('#')
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return '#{:02x}{:02x}{:02x}'.format(
        int(r * factor), int(g * factor), int(b * factor)
    )
