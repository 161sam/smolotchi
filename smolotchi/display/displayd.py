import time

from smolotchi.core.bus import SQLiteBus
from smolotchi.core.resources import ResourceManager

from .render import render_state
from .waveshare_driver import EPDDriver


def main() -> None:
    bus = SQLiteBus()
    resources = ResourceManager("/run/smolotchi/locks")

    owner = "displayd"
    have_display_lock = False

    driver = EPDDriver()
    ok_hw = driver.init()
    if ok_hw:
        driver.clear()

    last_state = None
    last_note = ""
    while True:
        have_display_lock = resources.acquire("display", owner=owner, ttl=20.0)
        if not have_display_lock:
            bus.publish("display.lock.denied", {"owner": owner})
        else:
            bus.publish("display.lock.ok", {"owner": owner})

        events = bus.tail(limit=10, topic_prefix="core.state.")
        for event in events:
            if event.topic == "core.state.changed":
                state = event.payload.get("state")
                note = event.payload.get("note", "")
                if state != last_state or note != last_note:
                    if ok_hw and have_display_lock:
                        width, height = driver.size
                        image = render_state(width, height, str(state), str(note))
                        driver.display_image(image)
                    last_state, last_note = state, note
                break
        time.sleep(1.0)


if __name__ == "__main__":
    main()
