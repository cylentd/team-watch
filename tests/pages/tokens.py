"""A colour token as the browser paints it (`rgb(...)`), so a test compares a drawn colour with the token it
should be without retyping the token's hex (tokens.css stays the one place a colour is spelled)."""

TOKEN_RGB = """name => { const d = document.createElement('i'); d.style.color = `var(${name})`; document.body.append(d);
  const c = getComputedStyle(d).color; d.remove(); return c; }"""


def token_rgb(page, name):
    """`token_rgb(page, "--line-2")` -> "rgb(52, 59, 70)"."""
    return page.evaluate(TOKEN_RGB, name)
