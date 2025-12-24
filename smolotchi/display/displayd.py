import time

from smolotchi.core.bus import SQLiteBus

from .render import render_state
from .waveshare_driver import EPDDriver


def main() -> None:
    bus = SQLiteBus()
    driver = EPDDriver()
    ok = driver.init()
    if ok:
        driver.clear()

    last_state = None
    last_note = ""
    while True:
        events = bus.tail(limit=10, topic_prefix="core.state.")
        for event in events:
            if event.topic == "core.state.changed":
                state = event.payload.get("state")
                note = event.payload.get("note", "")
                if state != last_state or note != last_note:
                    width, height = driver.size
                    image = render_state(width, height, str(state), str(note))
                    if ok:
                        driver.display_image(image)
                    last_state, last_note = state, note
                break
        time.sleep(1.0)


if __name__ == "__main__":
    main()
