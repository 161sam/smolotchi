from smolotchi.display.displayd import _render_text_screen


def test_render_text_screen_smoke():
    img = _render_text_screen(250, 122, ["hello", "world"])
    assert img.size == (250, 122)
