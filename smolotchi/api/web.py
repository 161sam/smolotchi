from flask import Flask, redirect, render_template, request, url_for

from smolotchi.core.bus import SQLiteBus
from smolotchi.core.policy import Policy
from smolotchi.core.state import SmolotchiCore


def create_app() -> Flask:
    app = Flask(__name__)
    bus = SQLiteBus()
    policy = Policy(allowed_tags=["lab-approved"])
    core = SmolotchiCore(bus=bus, policy=policy)

    def nav_active(endpoint: str) -> str:
        return "active" if request.endpoint == endpoint else ""

    @app.context_processor
    def inject_globals():
        return {"nav_active": nav_active}

    @app.get("/")
    def dashboard():
        events = bus.tail(limit=30)
        status_evt = next(
            (event for event in events if event.topic == "core.state.changed"), None
        )
        return render_template("dashboard.html", status_evt=status_evt, events=events)

    @app.get("/wifi")
    def wifi():
        events = bus.tail(limit=50, topic_prefix="wifi.")
        return render_template("wifi.html", events=events)

    @app.get("/lan")
    def lan():
        events = bus.tail(limit=50, topic_prefix="lan.")
        return render_template("lan.html", events=events)

    @app.get("/config")
    def config():
        return render_template("config.html")

    @app.get("/audit")
    def audit():
        events = bus.tail(limit=100)
        return render_template("audit.html", events=events)

    @app.post("/handoff")
    def handoff():
        tag = request.form.get("tag", "lab-approved")
        note = request.form.get("note", "")
        bus.publish("ui.handoff.request", {"tag": tag, "note": note})
        return redirect(url_for("dashboard"))

    @app.post("/lan_done")
    def lan_done():
        bus.publish("lan.done", {"note": "manual done"})
        return redirect(url_for("lan"))

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=8080, debug=False)
