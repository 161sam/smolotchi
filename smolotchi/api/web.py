from flask import Flask, redirect, render_template, request, url_for

from smolotchi.core.bus import SQLiteBus
from smolotchi.core.policy import Policy
from smolotchi.core.state import SmolotchiCore


def create_app() -> Flask:
    app = Flask(__name__)
    bus = SQLiteBus()
    policy = Policy(allowed_tags=["lab-approved"])
    core = SmolotchiCore(bus=bus, policy=policy)

    @app.get("/")
    def dashboard():
        core.tick()
        events = bus.tail(limit=30)
        return render_template("dashboard.html", status=core.status, events=events)

    @app.post("/handoff")
    def handoff():
        tag = request.form.get("tag", "lab-approved")
        note = request.form.get("note", "")
        bus.publish("ui.handoff.request", {"tag": tag, "note": note})
        return redirect(url_for("dashboard"))

    @app.post("/lan_done")
    def lan_done():
        bus.publish("lan.done", {"note": "manual done"})
        return redirect(url_for("dashboard"))

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=8080, debug=False)
