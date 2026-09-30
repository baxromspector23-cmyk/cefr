from .conftest import SUPER_PASS, SUPER_PHONE, login, make_center


def test_health(client):
    assert client.get("/health").json() == {"status": "ok"}


def test_super_admin_login_and_me(client):
    h = login(client, SUPER_PHONE, SUPER_PASS)
    me = client.get("/auth/me", headers=h).json()
    assert me["role"] == "super_admin" and me["center_id"] is None


def test_wrong_password_rejected(client):
    r = client.post("/auth/login", json={"phone": SUPER_PHONE, "password": "wrong"})
    assert r.status_code == 401


def test_login_rate_limit(client):
    for _ in range(5):
        client.post("/auth/login", json={"phone": SUPER_PHONE, "password": "wrong"})
    r = client.post("/auth/login", json={"phone": SUPER_PHONE, "password": SUPER_PASS})
    assert r.status_code == 429


def test_no_token_rejected(client):
    assert client.get("/auth/me").status_code == 401


def test_refresh_rotation(client):
    r = client.post("/auth/login", json={"phone": SUPER_PHONE, "password": SUPER_PASS}).json()
    ok = client.post("/auth/refresh", json={"refresh_token": r["refresh_token"]})
    assert ok.status_code == 200
    again = client.post("/auth/refresh", json={"refresh_token": r["refresh_token"]})
    assert again.status_code == 401  # eski refresh token qayta ishlamaydi


def test_only_super_admin_creates_centers(client):
    admin = make_center(client, "oxford", "+998901111111")
    r = client.post("/centers", headers=admin, json={
        "name": "X", "slug": "xx-center", "phone": "+998902222222",
        "admin_full_name": "Y Y", "admin_password": "Password123"})
    assert r.status_code == 403


def test_student_cannot_create_users(client):
    admin = make_center(client, "oxford", "+998901111111")
    client.post("/users", headers=admin, json={
        "full_name": "Ali Valiyev", "phone": "+998903333333", "password": "StudentPass1", "role": "student"})
    s = login(client, "+998903333333", "StudentPass1", "oxford")
    r = client.post("/users", headers=s, json={
        "full_name": "Hack Er", "phone": "+998904444444", "password": "Password123", "role": "student"})
    assert r.status_code == 403


def test_teacher_cannot_create_teacher_or_admin(client):
    admin = make_center(client, "oxford", "+998901111111")
    client.post("/users", headers=admin, json={
        "full_name": "Azizbek T", "phone": "+998905555555", "password": "TeacherPass1", "role": "teacher"})
    t = login(client, "+998905555555", "TeacherPass1", "oxford")
    for role in ("teacher", "center_admin", "super_admin"):
        r = client.post("/users", headers=t, json={
            "full_name": "Some One", "phone": "+998906666666", "password": "Password123", "role": role})
        assert r.status_code == 403
