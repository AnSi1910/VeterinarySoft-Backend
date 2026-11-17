from datetime import datetime, timedelta, timezone


def future_time():
    return (datetime.now(timezone.utc) + timedelta(days=3)).replace(microsecond=0).isoformat()


def test_health_and_swagger(client):
    assert client.get("/health").json() == {"status": "healthy"}
    spec = client.get("/openapi.json").json()
    assert "/api/pets" in spec["paths"]
    assert "/api/appointments" in spec["paths"]


def test_register_login_no_password_leak(client, owner):
    me = client.get("/api/users/me", headers=owner["headers"])
    assert me.status_code == 200
    assert me.json()["email"] == "owner@example.com"
    assert "password_hash" not in me.json()
    assert me.json()["role"] == "owner"
    assert client.post("/api/auth/login", data={"username": "owner@example.com", "password": "wrong"}).status_code == 401
    assert client.post("/api/auth/register", json={"email": "owner@example.com", "full_name": "Петро", "password": "abcdefgh"}).status_code == 409


def test_validation_and_auth(client):
    assert client.get("/api/pets").status_code == 401
    assert client.post("/api/auth/register", json={"email": "not-email", "full_name": "А", "password": "123"}).status_code == 422
    assert client.get("/api/users/me", headers={"Authorization": "Bearer bad.jwt"}).status_code == 401


def test_pets_are_private(client, owner, other_owner, pet):
    assert client.get("/api/pets", headers=owner["headers"]).json()[0]["id"] == pet["id"]
    assert client.get(f"/api/pets/{pet['id']}", headers=other_owner["headers"]).status_code == 404
    assert client.patch(f"/api/pets/{pet['id']}", json={"name": "Чужий"}, headers=other_owner["headers"]).status_code == 404
    update = client.patch(f"/api/pets/{pet['id']}", json={"name": "Мурчик"}, headers=owner["headers"])
    assert update.status_code == 200 and update.json()["name"] == "Мурчик"


def test_role_restrictions(client, owner, admin, vet):
    assert client.post("/api/veterinarians", json={"full_name": "Наталя", "specialization": "Хірург"}, headers=owner["headers"]).status_code == 403
    assert client.get("/api/users", headers=owner["headers"]).status_code == 403
    assert client.get("/api/users", headers=admin["headers"]).status_code == 200
    assert len(client.get("/api/veterinarians").json()) == 1


def test_booking_collision_cancellation_and_status(client, owner, admin, pet, vet):
    body = {"pet_id": pet["id"], "veterinarian_id": vet["id"], "starts_at": future_time(), "reason": "Огляд"}
    one = client.post("/api/appointments", json=body, headers=owner["headers"])
    assert one.status_code == 201, one.text
    assert one.json()["status"] == "pending"
    assert client.post("/api/appointments", json=body, headers=owner["headers"]).status_code == 409
    path = f"/api/appointments/{one.json()['id']}/status"
    assert client.patch(path, json={"status": "confirmed"}, headers=owner["headers"]).status_code == 403
    assert client.patch(path, json={"status": "confirmed"}, headers=admin["headers"]).status_code == 200
    assert client.patch(path, json={"status": "cancelled"}, headers=owner["headers"]).status_code == 200
    assert client.patch(path, json={"status": "confirmed"}, headers=admin["headers"]).status_code == 409
    # Cancelled reservations don't block the same slot.
    assert client.post("/api/appointments", json=body, headers=owner["headers"]).status_code == 201


def test_invalid_booking_time(client, owner, pet, vet):
    body = {"pet_id": pet["id"], "veterinarian_id": vet["id"], "starts_at": "2024-01-01T10:00:00+02:00"}
    assert client.post("/api/appointments", json=body, headers=owner["headers"]).status_code == 422
    body["starts_at"] = "2030-01-01T10:00:00"  # Missing timezone
    assert client.post("/api/appointments", json=body, headers=owner["headers"]).status_code == 422


def test_medical_records_owner_read_admin_write(client, owner, other_owner, admin, pet, vet):
    body = {"pet_id": pet["id"], "veterinarian_id": vet["id"], "visit_date": "2026-10-15", "diagnosis": "Плановий огляд", "treatment": "Спостереження"}
    assert client.post("/api/medical-records", json=body, headers=owner["headers"]).status_code == 403
    response = client.post("/api/medical-records", json=body, headers=admin["headers"])
    assert response.status_code == 201, response.text
    owner_view = client.get(f"/api/medical-records/pet/{pet['id']}", headers=owner["headers"])
    assert owner_view.status_code == 200 and len(owner_view.json()) == 1
    assert client.get(f"/api/medical-records/pet/{pet['id']}", headers=other_owner["headers"]).status_code == 404
    assert client.delete(f"/api/pets/{pet['id']}", headers=owner["headers"]).status_code == 409


def test_reminder_crud_and_isolation(client, owner, other_owner, pet):
    body = {"pet_id": pet["id"], "title": "Вакцинація", "remind_at": future_time()}
    response = client.post("/api/reminders", json=body, headers=owner["headers"])
    assert response.status_code == 201
    reminder_id = response.json()["id"]
    assert len(client.get("/api/reminders", headers=owner["headers"]).json()) == 1
    assert client.get("/api/reminders", headers=other_owner["headers"]).json() == []
    assert client.delete(f"/api/reminders/{reminder_id}", headers=other_owner["headers"]).status_code == 404
    assert client.delete(f"/api/reminders/{reminder_id}", headers=owner["headers"]).status_code == 204


def test_pet_delete_without_related_data(client, owner, pet):
    assert client.delete(f"/api/pets/{pet['id']}", headers=owner["headers"]).status_code == 204
    assert client.get("/api/pets", headers=owner["headers"]).json() == []


def test_deactivated_vet_not_bookable(client, owner, admin, pet, vet):
    path = f"/api/veterinarians/{vet['id']}/deactivate"
    assert client.patch(path, headers=admin["headers"]).status_code == 200
    body = {"pet_id": pet["id"], "veterinarian_id": vet["id"], "starts_at": future_time()}
    assert client.post("/api/appointments", json=body, headers=owner["headers"]).status_code == 404
