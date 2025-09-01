# Testing the Face Detection API

## Quick Start

### 1. Setup Environment

```bash
# Clone the repository
git clone https://github.com/AwesomeuncleB/image-thingy.git
cd image-thingy

# Create virtual environment
python -m venv .venv

# Activate virtual environment
# On Windows:
.venv\Scripts\activate
# On macOS/Linux:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Start the API Server

```bash
# Option 1: Using the startup script
python start_api.py

# Option 2: Direct uvicorn command
python -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

The API will be available at:
- **API Base URL**: http://127.0.0.1:8000
- **Interactive Docs**: http://127.0.0.1:8000/docs
- **Health Check**: http://127.0.0.1:8000/health

## Testing Methods

### Method 1: Interactive API Documentation (Recommended)

1. Open http://127.0.0.1:8000/docs in your browser
2. You'll see Swagger UI with all endpoints
3. Click "Try it out" on any endpoint to test it
4. Upload images and see responses in real-time

### Method 2: Using cURL Commands

```bash
# Health check
curl http://127.0.0.1:8000/health

# Get registered users
curl http://127.0.0.1:8000/users

# Register a user (replace with actual image file)
curl -X POST "http://127.0.0.1:8000/users/register" \
  -F "name=John Doe" \
  -F "photo=@path/to/photo.jpg"

# Process event photos
curl -X POST "http://127.0.0.1:8000/events/test_event/process-photos" \
  -F "photos=@photo1.jpg" \
  -F "photos=@photo2.jpg"
```

### Method 3: Using the Python Client

```python
from client import EventFaceDetectionClient

# Initialize client
client = EventFaceDetectionClient("http://127.0.0.1:8000")

# Test health
health = client.health_check()
print("API Health:", health)

# Register a user
result = client.register_user("John Doe", "path/to/john_photo.jpg")
print("User registered:", result)

# Get all users
users = client.get_registered_users()
print("Registered users:", users)

# Process event photos
results = client.process_event_photos("event_123", [
    "path/to/photo1.jpg",
    "path/to/photo2.jpg"
])
print("Processing results:", results)
```

### Method 4: Using Postman or Insomnia

1. Import the API by using the OpenAPI spec at: http://127.0.0.1:8000/openapi.json
2. Test endpoints with form data for file uploads

## Test Endpoints

### Core Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Root endpoint |
| GET | `/health` | Health check |
| GET | `/users` | Get all registered users |
| POST | `/users/register` | Register new user with photo |
| DELETE | `/users/{user_id}` | Delete a user |
| POST | `/events/{event_id}/process-photos` | Process event photos |
| GET | `/events/{event_id}/results` | Get processing results |

### Integration Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/events/{event_id}/user-photos/{user_id}` | Add photo to user account |
| POST | `/events/{event_id}/organizer-folder` | Create organizer folder |
| POST | `/events/{event_id}/tag-unknown-face` | Tag unknown face |

## Sample Test Flow

1. **Start the server**
   ```bash
   python start_api.py
   ```

2. **Check health**
   ```bash
   curl http://127.0.0.1:8000/health
   ```

3. **Register users** (use actual image files)
   ```bash
   curl -X POST "http://127.0.0.1:8000/users/register" \
     -F "name=Alice" \
     -F "photo=@alice.jpg"
   ```

4. **Process event photos**
   ```bash
   curl -X POST "http://127.0.0.1:8000/events/party2024/process-photos" \
     -F "photos=@group_photo1.jpg" \
     -F "photos=@group_photo2.jpg"
   ```

5. **Get results**
   ```bash
   curl http://127.0.0.1:8000/events/party2024/results
   ```

## Expected Responses

### Health Check Response
```json
{
  "status": "healthy",
  "registered_users": 0,
  "processed_events": 0,
  "timestamp": "2024-01-01T12:00:00"
}
```

### User Registration Response
```json
{
  "user_id": "uuid-here",
  "name": "John Doe",
  "message": "User registered successfully"
}
```

### Photo Processing Response
```json
{
  "event_id": "party2024",
  "processed_at": "2024-01-01T12:00:00",
  "user_photos": {
    "user_id_1": [
      {
        "photo_id": "photo_123",
        "filename": "group_photo1.jpg",
        "confidence": 0.85,
        "bounding_box": {"top": 100, "left": 50, "bottom": 200, "right": 150}
      }
    ]
  },
  "unrecognized_faces": [],
  "organizer_photos": [],
  "total_photos_processed": 2,
  "processing_stats": {
    "total_faces_detected": 3,
    "recognized_faces": 2,
    "unrecognized_faces": 1
  }
}
```

## Troubleshooting

### Common Issues

1. **Server won't start**
   - Check if port 8000 is available
   - Ensure virtual environment is activated
   - Verify all dependencies are installed

2. **Can't access endpoints**
   - Use `127.0.0.1:8000` instead of `localhost:8000`
   - Check firewall settings
   - Ensure server is running

3. **File upload errors**
   - Use actual image files (JPG, PNG)
   - Check file permissions
   - Ensure files aren't too large

### Debug Mode

Start the server with debug logging:
```bash
python -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload --log-level debug
```

## Performance Notes

- This is a demo version with simplified face detection
- For production, integrate with actual face recognition libraries
- Consider adding authentication and rate limiting
- Use a proper database instead of in-memory storage