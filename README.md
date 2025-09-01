# Event Face Detection API

A FastAPI-based face detection and recognition system for automatically tagging people in event photos and organizing them by person. Perfect for integration with social event applications.

## Features

- **RESTful API**: FastAPI-based backend with automatic OpenAPI documentation
- **Face Detection**: Detect faces in event photos using advanced ML models
- **Face Recognition**: Match detected faces to registered users with confidence scores
- **Auto-Tagging**: Automatically tag people in photos and add to their accounts
- **Batch Processing**: Process multiple event photos simultaneously
- **Organizer Folder**: Create separate folders for event organizers
- **Unrecognized Faces**: Handle unknown faces for manual tagging
- **Social App Integration**: Ready-to-use integration module for your existing app
- **Docker Support**: Containerized deployment with Docker Compose

## Quick Start

### Option 1: Direct Python Setup

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Start the API server**:
   ```bash
   python start_api.py
   ```

3. **Access the API**:
   - API: http://localhost:8000
   - Documentation: http://localhost:8000/docs
   - Health Check: http://localhost:8000/health

### Option 2: Docker Setup

1. **Build and run with Docker Compose**:
   ```bash
   docker-compose up --build
   ```

2. **Access the API**:
   - API: http://localhost:8000

## API Usage

### Using the Python Client

```python
from client import EventFaceDetectionClient

# Initialize client
client = EventFaceDetectionClient("http://localhost:8000")

# Register a user
result = client.register_user("John Doe", "path/to/john_photo.jpg")
print(f"User registered: {result['user_id']}")

# Process event photos
results = client.process_event_photos("event_123", [
    "path/to/photo1.jpg",
    "path/to/photo2.jpg"
])

print(f"Found {len(results['user_photos'])} users in photos")
```

### Using cURL

```bash
# Register a user
curl -X POST "http://localhost:8000/users/register" \
  -F "name=John Doe" \
  -F "photo=@john_photo.jpg"

# Process event photos
curl -X POST "http://localhost:8000/events/event_123/process-photos" \
  -F "photos=@photo1.jpg" \
  -F "photos=@photo2.jpg"

# Get results
curl "http://localhost:8000/events/event_123/results"
```

### Integration with Your Social App

Use the `SocialAppIntegration` class for seamless integration:

```python
from social_app_integration import SocialAppIntegration

integration = SocialAppIntegration(
    social_app_base_url="https://your-app.com",
    social_app_api_key="your-api-key"
)

# Sync users and process photos
await integration.sync_event_users("event_123")
await integration.process_event_photos_workflow("event_123", photo_urls)
```

## API Endpoints

### Core Endpoints

- `POST /users/register` - Register a new user with face photo
- `GET /users` - Get all registered users
- `DELETE /users/{user_id}` - Delete a user
- `POST /events/{event_id}/process-photos` - Process event photos
- `GET /events/{event_id}/results` - Get processing results
- `GET /health` - Health check

### Integration Endpoints

- `POST /events/{event_id}/user-photos/{user_id}` - Add photo to user account
- `POST /events/{event_id}/organizer-folder` - Create organizer folder
- `POST /events/{event_id}/tag-unknown-face` - Tag unknown face

### Your Social App Endpoints (to implement)

Your social app should implement these endpoints for full integration:

- `GET /api/events/{event_id}/attendees` - Get event attendees
- `POST /api/users/{user_id}/photos` - Add photo to user account
- `POST /api/events/{event_id}/organizer-folder` - Create organizer folder
- `POST /api/events/{event_id}/unrecognized-faces` - Submit unrecognized faces

## Workflow for Event Photo Processing

1. **Event Setup**: Organizer creates event in your social app
2. **User Registration**: Attendees register and upload profile photos
3. **Photo Upload**: Event photos are uploaded to this face detection system
4. **Processing**: System detects faces and matches them to registered users
5. **Auto-Tagging**: Photos are automatically added to users' accounts
6. **Organizer Review**: Unrecognized faces are flagged for manual tagging
7. **Folder Creation**: Organizer gets a folder with all event photos

## Technical Details

- **Face Detection**: Uses SSD MobileNet v1 for fast face detection
- **Face Recognition**: Uses FaceNet-based embeddings for recognition
- **Threshold**: Recognition confidence threshold set to 60%
- **Browser Support**: Works in modern browsers with WebRTC support
- **Privacy**: All processing happens client-side, no data sent to external servers

## Customization

### Adjust Recognition Threshold
In `face-detection.js`, modify the threshold:
```javascript
if (match.distance < 0.6) { // Lower = stricter matching
```

### Add More Face Models
You can add additional face-api.js models for better accuracy:
- Age and gender detection
- Facial expression recognition
- Face landmarks for better alignment

### Batch Processing
For large events, consider implementing:
- Progress bars for long processing times
- Chunked processing to prevent browser freezing
- Background processing with Web Workers

## Integration Examples

### React Integration
```javascript
import { EventFaceDetectionWithAPI } from './api-integration.js';

const faceDetector = new EventFaceDetectionWithAPI({
  baseUrl: process.env.REACT_APP_API_URL,
  apiKey: process.env.REACT_APP_API_KEY
});
```

### Node.js Backend Processing
For server-side processing, you can use:
- `@vladmandic/face-api` (Node.js version)
- Sharp for image processing
- Similar workflow but on the server

## Performance Tips

- **Image Size**: Resize large images before processing for better performance
- **Batch Size**: Process photos in batches of 5-10 for optimal performance
- **Model Loading**: Models are loaded once and cached
- **Memory Management**: Clear processed images from memory after use

## Troubleshooting

### Models Not Loading
- Check if `models` folder contains all required files
- Ensure you're serving the app from a web server (not file://)
- Check browser console for CORS errors

### Poor Recognition Accuracy
- Use high-quality, well-lit photos for registration
- Ensure faces are clearly visible and front-facing
- Adjust recognition threshold if needed

### Performance Issues
- Reduce image sizes before processing
- Process fewer photos at once
- Use a more powerful device for processing

## Security Considerations

- **API Keys**: Never expose API keys in client-side code in production
- **Image Privacy**: Consider implementing image encryption for sensitive events
- **User Consent**: Ensure users consent to face recognition processing
- **Data Retention**: Implement policies for how long face data is stored

## License

This project uses face-api.js which is licensed under MIT License.