import pytest
import requests
import io
from PIL import Image
import numpy as np

# Test configuration
API_BASE_URL = "http://localhost:8000"

class TestEventFaceDetectionAPI:
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test environment"""
        self.base_url = API_BASE_URL
        self.session = requests.Session()
    
    def create_test_image(self, width=200, height=200):
        """Create a test image for testing"""
        # Create a simple test image
        image = Image.new('RGB', (width, height), color='white')
        
        # Convert to bytes
        img_byte_arr = io.BytesIO()
        image.save(img_byte_arr, format='JPEG')
        img_byte_arr.seek(0)
        
        return img_byte_arr
    
    def test_health_check(self):
        """Test API health check"""
        response = self.session.get(f"{self.base_url}/health")
        assert response.status_code == 200
        
        data = response.json()
        assert "status" in data
        assert data["status"] == "healthy"
    
    def test_get_users_empty(self):
        """Test getting users when none are registered"""
        response = self.session.get(f"{self.base_url}/users")
        assert response.status_code == 200
        
        data = response.json()
        assert "users" in data
        assert isinstance(data["users"], list)
    
    def test_register_user(self):
        """Test user registration"""
        test_image = self.create_test_image()
        
        files = {'photo': ('test.jpg', test_image, 'image/jpeg')}
        data = {'name': 'Test User'}
        
        response = self.session.post(
            f"{self.base_url}/users/register",
            files=files,
            data=data
        )
        
        # Note: This might fail if no face is detected in the test image
        # In a real test, you'd use an actual photo with a face
        if response.status_code == 400 and "No face detected" in response.text:
            pytest.skip("No face detected in test image - expected for synthetic image")
        
        assert response.status_code == 200
        data = response.json()
        assert "user_id" in data
        assert data["name"] == "Test User"
    
    def test_process_photos_no_users(self):
        """Test processing photos when no users are registered"""
        test_image = self.create_test_image()
        
        files = [('photos', ('test1.jpg', test_image, 'image/jpeg'))]
        
        response = self.session.post(
            f"{self.base_url}/events/test_event/process-photos",
            files=files
        )
        
        assert response.status_code == 400
        assert "No users registered" in response.text
    
    def test_invalid_image_upload(self):
        """Test uploading invalid file type"""
        # Create a text file instead of image
        text_file = io.BytesIO(b"This is not an image")
        
        files = {'photo': ('test.txt', text_file, 'text/plain')}
        data = {'name': 'Test User'}
        
        response = self.session.post(
            f"{self.base_url}/users/register",
            files=files,
            data=data
        )
        
        assert response.status_code == 400
        assert "File must be an image" in response.text

# Integration test example
def test_full_workflow():
    """Test the complete workflow with real images"""
    # This test requires actual photos with faces
    # Skip if test images are not available
    
    import os
    test_images_dir = "test_images"
    
    if not os.path.exists(test_images_dir):
        pytest.skip("Test images directory not found")
    
    client = requests.Session()
    base_url = API_BASE_URL
    
    # 1. Register users
    user_photos = [
        ("John Doe", "john.jpg"),
        ("Jane Smith", "jane.jpg")
    ]
    
    registered_users = []
    
    for name, photo_file in user_photos:
        photo_path = os.path.join(test_images_dir, photo_file)
        if not os.path.exists(photo_path):
            continue
            
        with open(photo_path, 'rb') as f:
            files = {'photo': f}
            data = {'name': name}
            
            response = client.post(f"{base_url}/users/register", files=files, data=data)
            if response.status_code == 200:
                registered_users.append(response.json())
    
    # 2. Process event photos
    event_photos = ["event1.jpg", "event2.jpg"]
    
    files = []
    for photo_file in event_photos:
        photo_path = os.path.join(test_images_dir, photo_file)
        if os.path.exists(photo_path):
            files.append(('photos', open(photo_path, 'rb')))
    
    if files:
        try:
            response = client.post(f"{base_url}/events/test_event/process-photos", files=files)
            if response.status_code == 200:
                results = response.json()
                print("Processing results:", results)
                
                # 3. Get results
                response = client.get(f"{base_url}/events/test_event/results")
                assert response.status_code == 200
                
        finally:
            # Close files
            for _, f in files:
                f.close()

if __name__ == "__main__":
    # Run basic tests
    test_api = TestEventFaceDetectionAPI()
    test_api.setup()
    
    try:
        test_api.test_health_check()
        print("✓ Health check passed")
        
        test_api.test_get_users_empty()
        print("✓ Get users test passed")
        
        test_api.test_invalid_image_upload()
        print("✓ Invalid image test passed")
        
        print("All basic tests passed!")
        
    except Exception as e:
        print(f"Test failed: {e}")