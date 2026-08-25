from copy import deepcopy

import pytest
from fastapi.testclient import TestClient

from src.app import activities, app


@pytest.fixture(autouse=True)
def restore_activities():
    original_activities = deepcopy(activities)
    yield
    activities.clear()
    activities.update(original_activities)


def test_root_redirects_to_static_page():
    # Arrange
    client = TestClient(app)

    # Act
    response = client.get("/", follow_redirects=False)

    # Assert
    assert response.status_code == 307
    assert response.headers["location"] == "/static/index.html"


def test_static_page_is_served():
    # Arrange
    client = TestClient(app)

    # Act
    response = client.get("/static/index.html")

    # Assert
    assert response.status_code == 200
    assert "Mergington High School" in response.text


def test_get_activities_returns_activity_details():
    # Arrange
    client = TestClient(app)

    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    activity = response.json()["Chess Club"]
    assert activity["description"]
    assert activity["schedule"]
    assert activity["max_participants"] == 12
    assert activity["participants"] == [
        "michael@mergington.edu",
        "daniel@mergington.edu",
    ]


def test_signup_adds_participant():
    # Arrange
    client = TestClient(app)
    email = "new.student@mergington.edu"

    # Act
    response = client.post(
        "/activities/Chess Club/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 200
    assert email in activities["Chess Club"]["participants"]
    assert response.json() == {
        "message": f"Signed up {email} for Chess Club"
    }


def test_signup_rejects_unknown_activity():
    # Arrange
    client = TestClient(app)

    # Act
    response = client.post(
        "/activities/Unknown Club/signup",
        params={"email": "student@mergington.edu"},
    )

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_signup_rejects_duplicate_participant():
    # Arrange
    client = TestClient(app)
    email = "michael@mergington.edu"

    # Act
    response = client.post(
        "/activities/Chess Club/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 400
    assert response.json()["detail"] == (
        "Student already signed up for this activity"
    )


def test_signup_requires_email():
    # Arrange
    client = TestClient(app)

    # Act
    response = client.post("/activities/Chess Club/signup")

    # Assert
    assert response.status_code == 422


def test_unregister_removes_participant():
    # Arrange
    client = TestClient(app)
    email = "michael@mergington.edu"

    # Act
    response = client.delete(
        "/activities/Chess Club/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 200
    assert email not in activities["Chess Club"]["participants"]
    assert response.json() == {
        "message": f"Unregistered {email} from Chess Club"
    }


def test_unregister_rejects_unknown_activity():
    # Arrange
    client = TestClient(app)

    # Act
    response = client.delete(
        "/activities/Unknown Club/signup",
        params={"email": "student@mergington.edu"},
    )

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_unregister_rejects_missing_participant():
    # Arrange
    client = TestClient(app)

    # Act
    response = client.delete(
        "/activities/Chess Club/signup",
        params={"email": "not.signed.up@mergington.edu"},
    )

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == (
        "Student is not signed up for this activity"
    )
