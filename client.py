import requests
import json
from typing import List, Optional
import os

class EventFaceDetectionClient:
    """Client for interacting with the Event Face Detection API"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
    
    def register_user(self, name: str, photo_path: str, user_id: Optional[str] = None) -> dict:
        """Register a new user with their face photo"""
        url = f"{self.base_url}/users/register"
        
        with open(photo_path, 'rb') as photo_file:
            files = {'photo': photo_file}
            data = {'name': name}
            if user_id:
                data['user_id'] = user_id
            
            response = self.session.post(url, files=files, data=data)
            response.raise_for_status()
            return response.json()
    
    def get_registered_users(self) -> dict:
        """Get all registered users"""
        url = f"{self.base_url}/users"
        response = self.session.get(url)
        response.raise_for_status()
        return response.json()
    
    def delete_user(self, user_id: str) -> dict:
        """Delete a registered user"""
        url = f"{self.base_url}/users/{user_id}"
        response = self.session.delete(url)
        response.raise_for_status()
        return response.json()
    
    def process_event_photos(self, event_id: str, photo_paths: List[str]) -> dict:
        """Process multiple event photos for face detection"""
        url = f"{self.base_url}/events/{event_id}/process-photos"
        
        files = []
        try:
            for photo_path in photo_paths:
                files.append(('photos', open(photo_path, 'rb')))
            
            response = self.session.post(url, files=files)
            response.raise_for_status()
            return response.json()
        finally:
            # Close all opened files
            for _, file_obj in files:
                file_obj.close()
    
    def get_event_results(self, event_id: str) -> dict:
        """Get processing results for an event"""
        url = f"{self.base_url}/events/{event_id}/results"
        response = self.session.get(url)
        response.raise_for_status()
        return response.json()
    
    def add_photo_to_user(self, event_id: str, user_id: str, photo_id: str, 
                         confidence: float, metadata: Optional[dict] = None) -> dict:
        """Add a photo to a user's account"""
        url = f"{self.base_url}/events/{event_id}/user-photos/{user_id}"
        
        data = {
            'photo_id': photo_id,
            'confidence': confidence
        }
        if metadata:
            data['metadata'] = json.dumps(metadata)
        
        response = self.session.post(url, data=data)
        response.raise_for_status()
        return response.json()
    
    def tag_unknown_face(self, event_id: str, face_id: str, user_name: str, 
                        create_new_user: bool = False) -> dict:
        """Tag an unknown face with a user name"""
        url = f"{self.base_url}/events/{event_id}/tag-unknown-face"
        
        data = {
            'face_id': face_id,
            'user_name': user_name,
            'create_new_user': create_new_user
        }
        
        response = self.session.post(url, data=data)
        response.raise_for_status()
        return response.json()
    
    def health_check(self) -> dict:
        """Check API health"""
        url = f"{self.base_url}/health"
        response = self.session.get(url)
        response.raise_for_status()
        return response.json()

# Example usage
if __name__ == "__main__":
    client = EventFaceDetectionClient()
    
    # Example workflow
    try:
        # Check API health
        health = client.health_check()
        print("API Health:", health)
        
        # Register a user (you'll need actual photo files)
        # result = client.register_user("John Doe", "path/to/john_photo.jpg")
        # print("User registered:", result)
        
        # Get registered users
        users = client.get_registered_users()
        print("Registered users:", users)
        
        # Process event photos (you'll need actual photo files)
        # event_results = client.process_event_photos("event123", [
        #     "path/to/event_photo1.jpg",
        #     "path/to/event_photo2.jpg"
        # ])
        # print("Event processing results:", event_results)
        
    except requests.exceptions.RequestException as e:
        print(f"API Error: {e}")
    except Exception as e:
        print(f"Error: {e}")