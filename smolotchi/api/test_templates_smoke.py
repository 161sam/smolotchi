def test_templates_smoke(client):
    r = client.get("/")
    assert r.status_code in (200, 302)

    r = client.get("/ai/plans")
    assert r.status_code in (200, 302)

    r = client.get("/ai/stages")
    assert r.status_code in (200, 302)
