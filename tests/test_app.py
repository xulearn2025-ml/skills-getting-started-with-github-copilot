import sys
from pathlib import Path

# Add src directory to path so we can import app
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from fastapi.testclient import TestClient
from app import app


client = TestClient(app)


class TestGetActivities:
    """Tests for the GET /activities endpoint"""
    
    def test_get_activities_returns_200(self):
        """Test that GET /activities returns status 200"""
        response = client.get("/activities")
        assert response.status_code == 200
    
    def test_get_activities_returns_dict(self):
        """Test that GET /activities returns a dictionary"""
        response = client.get("/activities")
        assert isinstance(response.json(), dict)
    
    def test_get_activities_contains_basketball(self):
        """Test that activities include Basketball"""
        response = client.get("/activities")
        activities = response.json()
        assert "Basketball" in activities
    
    def test_get_activities_has_activity_details(self):
        """Test that each activity has required fields"""
        response = client.get("/activities")
        activities = response.json()
        basketball = activities["Basketball"]
        
        assert "description" in basketball
        assert "schedule" in basketball
        assert "max_participants" in basketball
        assert "participants" in basketball
    
    def test_get_activities_has_all_activities(self):
        """Test that all expected activities are present"""
        response = client.get("/activities")
        activities = response.json()
        expected = [
            "Basketball", "Tennis Club", "Art Studio", "Music Band",
            "Debate Team", "Science Club", "Chess Club",
            "Programming Class", "Gym Class"
        ]
        for activity in expected:
            assert activity in activities


class TestSignupForActivity:
    """Tests for the POST /activities/{activity_name}/signup endpoint"""
    
    def test_signup_for_existing_activity(self, reset_activities):
        """Test signing up for an existing activity"""
        response = client.post(
            "/activities/Basketball/signup",
            params={"email": "newstudent@mergington.edu"}
        )
        assert response.status_code == 200
        assert "Signed up" in response.json()["message"]
    
    def test_signup_adds_participant(self, reset_activities):
        """Test that signup adds participant to the activity"""
        client.post(
            "/activities/Basketball/signup",
            params={"email": "newstudent@mergington.edu"}
        )
        
        response = client.get("/activities")
        activities = response.json()
        assert "newstudent@mergington.edu" in activities["Basketball"]["participants"]
    
    def test_signup_for_nonexistent_activity(self):
        """Test signing up for a non-existent activity returns 404"""
        response = client.post(
            "/activities/NonExistent/signup",
            params={"email": "student@mergington.edu"}
        )
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]
    
    def test_signup_already_registered_student(self):
        """Test signing up an already registered student returns 400"""
        response = client.post(
            "/activities/Basketball/signup",
            params={"email": "james@mergington.edu"}
        )
        assert response.status_code == 400
        assert "already signed up" in response.json()["detail"]
    
    def test_signup_multiple_students(self, reset_activities):
        """Test signing up multiple students for the same activity"""
        student1 = "student1@mergington.edu"
        student2 = "student2@mergington.edu"
        
        response1 = client.post(
            "/activities/Tennis Club/signup",
            params={"email": student1}
        )
        response2 = client.post(
            "/activities/Tennis Club/signup",
            params={"email": student2}
        )
        
        assert response1.status_code == 200
        assert response2.status_code == 200
        
        response = client.get("/activities")
        activities = response.json()
        assert student1 in activities["Tennis Club"]["participants"]
        assert student2 in activities["Tennis Club"]["participants"]


class TestUnregisterParticipant:
    """Tests for the DELETE /unregister endpoint"""
    
    def test_unregister_existing_participant(self, reset_activities):
        """Test unregistering an existing participant"""
        response = client.delete(
            "/unregister",
            params={"participant": "james@mergington.edu", "activity": "Basketball"}
        )
        assert response.status_code == 200
        assert "Unregistered" in response.json()["message"]
    
    def test_unregister_removes_participant(self, reset_activities):
        """Test that unregister removes participant from the activity"""
        client.delete(
            "/unregister",
            params={"participant": "james@mergington.edu", "activity": "Basketball"}
        )
        
        response = client.get("/activities")
        activities = response.json()
        assert "james@mergington.edu" not in activities["Basketball"]["participants"]
    
    def test_unregister_nonexistent_activity(self):
        """Test unregistering from a non-existent activity returns 404"""
        response = client.delete(
            "/unregister",
            params={"participant": "student@mergington.edu", "activity": "NonExistent"}
        )
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]
    
    def test_unregister_nonexistent_participant(self):
        """Test unregistering a non-existent participant returns 404"""
        response = client.delete(
            "/unregister",
            params={"participant": "nonexistent@mergington.edu", "activity": "Basketball"}
        )
        assert response.status_code == 404
        assert "Participant not found" in response.json()["detail"]
    
    def test_unregister_participant_from_multiple_activities(self, reset_activities):
        """Test unregistering a participant from one activity doesn't affect others"""
        # Sign up for two activities
        client.post(
            "/activities/Basketball/signup",
            params={"email": "student@mergington.edu"}
        )
        client.post(
            "/activities/Tennis Club/signup",
            params={"email": "student@mergington.edu"}
        )
        
        # Unregister from Basketball
        client.delete(
            "/unregister",
            params={"participant": "student@mergington.edu", "activity": "Basketball"}
        )
        
        response = client.get("/activities")
        activities = response.json()
        
        # Should not be in Basketball
        assert "student@mergington.edu" not in activities["Basketball"]["participants"]
        
        # Should still be in Tennis Club
        assert "student@mergington.edu" in activities["Tennis Club"]["participants"]
