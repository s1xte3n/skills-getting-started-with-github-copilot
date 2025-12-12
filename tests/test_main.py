"""Tests for the Mergington High School Activities API."""

import pytest


class TestActivitiesAPI:
    """Test suite for activities endpoints."""

    def test_root_redirect(self, client):
        """Test that root endpoint redirects to static files."""
        # TestClient follows redirects by default, so we need to disable it
        client.follow_redirects = False
        response = client.get("/")
        assert response.status_code == 307  # Temporary redirect
        assert "/static/index.html" in response.headers["location"]
        client.follow_redirects = True  # Reset for other tests

    def test_get_activities(self, client):
        """Test getting all activities."""
        response = client.get("/activities")
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, dict)
        assert len(data) > 0  # Should have activities

        # Check structure of first activity
        first_activity = next(iter(data.values()))
        assert "description" in first_activity
        assert "schedule" in first_activity
        assert "max_participants" in first_activity
        assert "participants" in first_activity
        assert isinstance(first_activity["participants"], list)

    def test_signup_success(self, client):
        """Test successful signup for an activity."""
        # Use an activity that exists
        response = client.get("/activities")
        activities = response.json()
        activity_name = list(activities.keys())[0]  # Get first activity

        # Get initial participant count
        initial_count = len(activities[activity_name]["participants"])

        # Sign up a new student
        email = "test@example.com"
        response = client.post(f"/activities/{activity_name}/signup?email={email}")

        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert email in data["message"]

        # Verify participant was added
        response = client.get("/activities")
        activities = response.json()
        assert len(activities[activity_name]["participants"]) == initial_count + 1
        assert email in activities[activity_name]["participants"]

    def test_signup_already_registered(self, client):
        """Test signup when student is already registered."""
        # Get an activity with existing participants
        response = client.get("/activities")
        activities = response.json()

        # Find an activity with participants
        activity_name = None
        existing_email = None
        for name, details in activities.items():
            if details["participants"]:
                activity_name = name
                existing_email = details["participants"][0]
                break

        if not activity_name:
            pytest.skip("No activity with existing participants found")

        # Try to sign up the same student again
        response = client.post(f"/activities/{activity_name}/signup?email={existing_email}")
        assert response.status_code == 400
        data = response.json()
        assert "already signed up" in data["detail"].lower()

    def test_signup_activity_not_found(self, client):
        """Test signup for non-existent activity."""
        response = client.post("/activities/NonExistentActivity/signup?email=test@example.com")
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()

    def test_unregister_success(self, client):
        """Test successful unregister from an activity."""
        # First, sign up a student
        response = client.get("/activities")
        activities = response.json()
        activity_name = list(activities.keys())[0]

        email = "unregister-test@example.com"
        client.post(f"/activities/{activity_name}/signup?email={email}")

        # Get count after signup
        response = client.get("/activities")
        activities = response.json()
        count_after_signup = len(activities[activity_name]["participants"])

        # Now unregister
        response = client.delete(f"/activities/{activity_name}/unregister?email={email}")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert email in data["message"]

        # Verify participant was removed
        response = client.get("/activities")
        activities = response.json()
        assert len(activities[activity_name]["participants"]) == count_after_signup - 1
        assert email not in activities[activity_name]["participants"]

    def test_unregister_not_registered(self, client):
        """Test unregister when student is not registered."""
        response = client.get("/activities")
        activities = response.json()
        activity_name = list(activities.keys())[0]

        email = "not-registered@example.com"
        response = client.delete(f"/activities/{activity_name}/unregister?email={email}")
        assert response.status_code == 400
        data = response.json()
        assert "not signed up" in data["detail"].lower()

    def test_unregister_activity_not_found(self, client):
        """Test unregister from non-existent activity."""
        response = client.delete("/activities/NonExistentActivity/unregister?email=test@example.com")
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()