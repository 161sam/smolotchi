class EPDDriver:
    """
    Abstraktion, damit Smolotchi ohne Display booten kann.
    """

    def __init__(self):
        self.epd = None

    def init(self) -> bool:
        try:
            from waveshare_epd import epd2in13_V4

            self.epd = epd2in13_V4.EPD()
            self.epd.init()
            return True
        except Exception:
            self.epd = None
            return False

    @property
    def size(self):
        if self.epd:
            return (self.epd.width, self.epd.height)
        return (250, 122)

    def clear(self):
        if self.epd:
            self.epd.Clear(0xFF)

    def display_image(self, image):
        if self.epd:
            self.epd.display(self.epd.getbuffer(image))
