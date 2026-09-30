from .conftest import SUPER_PASS, SUPER_PHONE, login, make_center


def _student(client, admin, phone, name="Student One"):
    r = client.post("/users", headers=admin, json={
        "full_name": name, "phone": phone, "password": "StudentPass1", "role": "student"})
    assert r.status_code == 201, r.text
    return r.json()


def test_centers_cannot_see_each_others_users(client):
    a = make_center(client, "center-a", "+998901000001")
    b = make_center(client, "center-b", "+998901000002")
    sa = _student(client, a, "+998907000001", "A Student")
    _student(client, b, "+998907000002", "B Student")

    names_a = {u["full_name"] for u in client.get("/users", headers=a).json()}
    names_b = {u["full_name"] for u in client.get("/users", headers=b).json()}
    assert "A Student" in names_a and "B Student" not in names_a
    assert "B Student" in names_b and "A Student" not in names_b

    # B admin A ning o'quvchisini ID orqali ham ko'ra olmaydi
    assert client.get(f"/users/{sa['id']}", headers=b).status_code == 404


def test_same_phone_allowed_in_different_centers(client):
    a = make_center(client, "center-a", "+998901000001")
    b = make_center(client, "center-b", "+998901000002")
    _student(client, a, "+998909999999")
    _student(client, b, "+998909999999")  # 409 bo'lmasligi kerak


def test_duplicate_phone_in_same_center_rejected(client):
    a = make_center(client, "center-a", "+998901000001")
    _student(client, a, "+998909999999")
    r = client.post("/users", headers=a, json={
        "full_name": "Dup", "phone": "+998909999999", "password": "StudentPass1", "role": "student"})
    assert r.status_code == 409


def test_login_requires_correct_center(client):
    a = make_center(client, "center-a", "+998901000001")
    make_center(client, "center-b", "+998901000002")
    _student(client, a, "+998907000001")
    r = client.post("/auth/login", json={"phone": "+998907000001", "password": "StudentPass1",
                                         "center_slug": "center-b"})
    assert r.status_code == 401


def test_deactivated_center_is_locked_out(client):
    a = make_center(client, "center-a", "+998901000001")
    sup = login(client, SUPER_PHONE, SUPER_PASS)
    cid = client.get("/auth/me", headers=a).json()["center_id"]
    assert client.patch(f"/centers/{cid}/active?active=false", headers=sup).status_code == 200
    assert client.get("/auth/me", headers=a).status_code == 403
