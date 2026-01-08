class EPDDriver:
    """
    Abstraktion, damit Smolotchi ohne Display booten kann.
    Hält den letzten Fehler zur Diagnose.
    """

    def __init__(self):
        self.epd = None
        self.last_error: str = ""

    def init(self) -> bool:
        self.last_error = ""
        try:
            # Force gpiozero to NOT use sysfs/native and NOT pick Jetson paths
            from gpiozero import Device
            try:
                from gpiozero.pins.lgpio import LGPIOFactory
                Device.pin_factory = LGPIOFactory()
            except Exception:
                from gpiozero.pins.rpigpio import RPiGPIOFactory
                Device.pin_factory = RPiGPIOFactory()

            # Try common 2.13" modules (different revisions)
            candidates = ["epd2in13_V4", "epd2in13_V3", "epd2in13_V2", "epd2in13"]
            last = None
            for name in candidates:
                try:
                    mod = __import__(f"waveshare_epd.{name}", fromlist=["EPD"])
                    self.epd = mod.EPD()
                    self.epd.init()
                    return True
                except Exception as e:
                    last = (name, e)
                    self.epd = None
            if last:
                n, e = last
                raise Exception(f"all epd2in13 candidates failed (last={n}: {type(e).__name__}: {e})")
        except Exception as ex:
            self.last_error = f"{type(ex).__name__}: {ex}"
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
