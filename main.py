from fastapi import FastAPI, File, UploadFile, HTTPException, Depends, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import List, Optional, Dict, Any
import numpy as np
from PIL import Image, ImageDraw
import io
import base64
import json
import os
from datetime import datetime
import uuid
from pydantic import BaseModel
import aiofiles
import hashlib
import random

app = FastAPI(
    title="Event Face Detection API",
    description="Face detection and recognition system for social events",
    version="1.0.0"
)

# CORS middleware for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Data models
class UserRegistration(BaseModel):
    name: str
    user_id: Optional[str] = None

class FaceMatch(BaseModel):
    user_id: str
    user_name: str
    confidence: float
    bounding_box: Dict[str, int]

class PhotoResult(BaseModel):
    photo_id: str
    recognized_faces: List[FaceMatch]
    unrecognized_faces: List[Dict[str, Any]]
    total_faces: int

class EventProcessingResult(BaseModel):
    event_id: str
    processed_at: str
    user_photos: Dict[str, List[Dict[str, Any]]]
    unrecognized_faces: List[Dict[str, Any]]
    organizer_photos: List[Dict[str, Any]]
    total_photos_processed: int
    processing_stats: Dict[str, Any]

# In-memory storage (use database in production)
registered_users = {}
face_encodings_db = {}
processing_results = {}

class FaceDetectionService:
    def __init__(self):
        self.recognition_threshold = 0.7
        
    def load_image_from_bytes(self, image_bytes: bytes) -> Image.Image:
        """Load image from bytes"""
        image = Image.open(io.BytesIO(image_bytes))
        if image.mode != 'RGB':
            image = image.convert('RGB')
        return image
    
    def create_image_hash(self, image: Image.Image) -> str:
        """Create a simple hash of the image for basic comparison"""
        # Resize to standard size for comparison
        resized = image.resize((64, 64))
        # Convert to grayscale
        gray = resized.convert('L')
        # Get pixel data
        pixels = list(gray.getdata())
        # Create hash
        hash_str = hashlib.md5(str(pixels).encode()).hexdigest()
        return hash_str
    
    def detect_faces_simple(self, image: Image.Image) -> list:
        """Simple face detection simulation - detects image regions that could contain faces"""
        width, height = image.size
        
        # Simulate face detection by creating random bounding boxes
        # In a real implementation, this would use actual face detection
        faces = []
        
        # For demo purposes, let's assume we find 1-3 faces in random locations
        num_faces = random.randint(1, min(3, max(1, width // 200)))
        
        for i in range(num_faces):
            # Random face location (ensuring it's within image bounds)
            face_size = random.randint(80, min(200, width // 3, height // 3))
            left = random.randint(0, max(0, width - face_size))
            top = random.randint(0, max(0, height - face_size))
            right = left + face_size
            bottom = top + face_size
            
            faces.append({
                'left': left,
                'top': top,
                'right': right,
                'bottom': bottom
            })
        
        return faces
    
    def register_user_face(self, user_id: str, name: str, image_bytes: bytes) -> bool:
        """Register a user's face"""
        try:
            image = self.load_image_from_bytes(image_bytes)
            
            # Create a simple "face encoding" using image hash and basic features
            face_hash = self.create_image_hash(image)
            
            # Store basic image features
            width, height = image.size
            
            registered_users[user_id] = {
                'name': name,
                'registered_at': datetime.now().isoformat(),
                'face_hash': face_hash,
                'image_features': {
                    'width': width,
                    'height': height,
                    'aspect_ratio': width / height if height > 0 else 1.0
                }
            }
            
            face_encodings_db[user_id] = {
                'hash': face_hash,
                'features': registered_users[user_id]['image_features']
            }
            
            return True
            
        except Exception as e:
            print(f"Error registering user: {e}")
            return False
    
    def recognize_faces(self, image: Image.Image) -> tuple:
        """Recognize faces in image and return matches"""
        face_locations = self.detect_faces_simple(image)
        
        recognized_faces = []
        unrecognized_faces = []
        
        for i, face_location in enumerate(face_locations):
            # Extract face region
            left = face_location['left']
            top = face_location['top']
            right = face_location['right']
            bottom = face_location['bottom']
            
            face_image = image.crop((left, top, right, bottom))
            
            # Try to match with registered users
            best_match = self.find_best_match_simple(face_image)
            
            if best_match:
                recognized_faces.append({
                    'user_id': best_match['user_id'],
                    'user_name': best_match['name'],
                    'confidence': best_match['confidence'],
                    'bounding_box': {
                        'top': top,
                        'right': right,
                        'bottom': bottom,
                        'left': left
                    }
                })
            else:
                # Convert face image to base64
                buffer = io.BytesIO()
                face_image.save(buffer, format='JPEG')
                face_base64 = base64.b64encode(buffer.getvalue()).decode()
                
                unrecognized_faces.append({
                    'face_id': str(uuid.uuid4()),
                    'face_image': face_base64,
                    'bounding_box': {
                        'top': top,
                        'right': right,
                        'bottom': bottom,
                        'left': left
                    }
                })
        
        return recognized_faces, unrecognized_faces
    
    def find_best_match_simple(self, face_image: Image.Image) -> Optional[Dict]:
        """Find best matching registered user using simple comparison"""
        if not face_encodings_db:
            return None
        
        face_hash = self.create_image_hash(face_image)
        width, height = face_image.size
        face_features = {
            'width': width,
            'height': height,
            'aspect_ratio': width / height if height > 0 else 1.0
        }
        
        best_match = None
        best_score = 0
        
        for user_id, user_data in face_encodings_db.items():
            # Simple similarity scoring
            score = 0
            
            # Hash similarity (simplified)
            if user_data['hash'] == face_hash:
                score += 0.8
            
            # Feature similarity
            stored_features = user_data['features']
            aspect_diff = abs(face_features['aspect_ratio'] - stored_features['aspect_ratio'])
            if aspect_diff < 0.2:
                score += 0.2
            
            # Add some randomness to simulate real face recognition confidence
            score += random.uniform(-0.1, 0.1)
            
            if score > best_score and score > self.recognition_threshold:
                best_score = score
                best_match = {
                    'user_id': user_id,
                    'name': registered_users[user_id]['name'],
                    'confidence': min(0.99, score)
                }
        
        return best_match

# Initialize face detection service
face_service = FaceDetectionService()

@app.get("/")
async def root():
    return {"message": "Event Face Detection API", "version": "1.0.0"}

@app.post("/users/register")
async def register_user(
    name: str = Form(...),
    user_id: Optional[str] = Form(None),
    photo: UploadFile = File(...)
):
    """Register a new user with their face photo"""
    if not user_id:
        user_id = str(uuid.uuid4())
    
    if user_id in registered_users:
        raise HTTPException(status_code=400, detail="User already registered")
    
    # Validate image file
    if not photo.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    try:
        image_bytes = await photo.read()
        success = face_service.register_user_face(user_id, name, image_bytes)
        
        if not success:
            raise HTTPException(status_code=400, detail="No face detected in image")
        
        return {
            "user_id": user_id,
            "name": name,
            "message": "User registered successfully"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Registration failed: {str(e)}")

@app.get("/users")
async def get_registered_users():
    """Get all registered users"""
    users = []
    for user_id, user_data in registered_users.items():
        users.append({
            "user_id": user_id,
            "name": user_data["name"],
            "registered_at": user_data["registered_at"]
        })
    return {"users": users}

@app.delete("/users/{user_id}")
async def delete_user(user_id: str):
    """Delete a registered user"""
    if user_id not in registered_users:
        raise HTTPException(status_code=404, detail="User not found")
    
    del registered_users[user_id]
    del face_encodings_db[user_id]
    
    return {"message": "User deleted successfully"}

@app.post("/events/{event_id}/process-photos")
async def process_event_photos(
    event_id: str,
    photos: List[UploadFile] = File(...)
):
    """Process multiple event photos for face detection and recognition"""
    if not registered_users:
        raise HTTPException(status_code=400, detail="No users registered")
    
    results = {
        "user_photos": {},  # user_id -> list of photos they appear in
        "unrecognized_faces": [],
        "organizer_photos": [],
        "photo_results": []
    }
    
    try:
        for i, photo in enumerate(photos):
            if not photo.content_type.startswith('image/'):
                continue
            
            photo_id = f"{event_id}_photo_{i}_{uuid.uuid4()}"
            image_bytes = await photo.read()
            image = face_service.load_image_from_bytes(image_bytes)
            
            # Process the photo
            recognized_faces, unrecognized_faces = face_service.recognize_faces(image)
            
            # Store photo result
            photo_result = {
                "photo_id": photo_id,
                "filename": photo.filename,
                "recognized_faces": recognized_faces,
                "unrecognized_faces": unrecognized_faces,
                "total_faces": len(recognized_faces) + len(unrecognized_faces)
            }
            results["photo_results"].append(photo_result)
            
            # Organize by user
            for face in recognized_faces:
                user_id = face["user_id"]
                if user_id not in results["user_photos"]:
                    results["user_photos"][user_id] = []
                
                results["user_photos"][user_id].append({
                    "photo_id": photo_id,
                    "filename": photo.filename,
                    "confidence": face["confidence"],
                    "bounding_box": face["bounding_box"]
                })
            
            # Add unrecognized faces
            for face in unrecognized_faces:
                face["photo_id"] = photo_id
                face["filename"] = photo.filename
                results["unrecognized_faces"].append(face)
            
            # Add to organizer photos if it has faces
            if photo_result["total_faces"] > 0:
                results["organizer_photos"].append({
                    "photo_id": photo_id,
                    "filename": photo.filename,
                    "total_faces": photo_result["total_faces"]
                })
        
        # Store results for later retrieval
        processing_result = EventProcessingResult(
            event_id=event_id,
            processed_at=datetime.now().isoformat(),
            user_photos=results["user_photos"],
            unrecognized_faces=results["unrecognized_faces"],
            organizer_photos=results["organizer_photos"],
            total_photos_processed=len(photos),
            processing_stats={
                "total_faces_detected": sum(r["total_faces"] for r in results["photo_results"]),
                "recognized_faces": sum(len(r["recognized_faces"]) for r in results["photo_results"]),
                "unrecognized_faces": len(results["unrecognized_faces"])
            }
        )
        
        processing_results[event_id] = processing_result.dict()
        
        return processing_result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")

@app.get("/events/{event_id}/results")
async def get_event_results(event_id: str):
    """Get processing results for an event"""
    if event_id not in processing_results:
        raise HTTPException(status_code=404, detail="Event results not found")
    
    return processing_results[event_id]

@app.post("/events/{event_id}/user-photos/{user_id}")
async def add_photo_to_user(
    event_id: str,
    user_id: str,
    photo_id: str = Form(...),
    confidence: float = Form(...),
    metadata: Optional[str] = Form(None)
):
    """Add a photo to a user's account (for social app integration)"""
    if user_id not in registered_users:
        raise HTTPException(status_code=404, detail="User not found")
    
    # This would integrate with your social app's database
    # For now, we'll just return success
    return {
        "message": f"Photo {photo_id} added to user {user_id}",
        "event_id": event_id,
        "confidence": confidence
    }

@app.post("/events/{event_id}/organizer-folder")
async def create_organizer_folder(
    event_id: str,
    photos: List[UploadFile] = File(...)
):
    """Create organizer folder with event photos"""
    # This would integrate with your social app's file storage
    # For now, we'll just return the photo count
    return {
        "message": f"Organizer folder created for event {event_id}",
        "photo_count": len(photos),
        "folder_id": f"organizer_{event_id}_{uuid.uuid4()}"
    }

@app.post("/events/{event_id}/tag-unknown-face")
async def tag_unknown_face(
    event_id: str,
    face_id: str = Form(...),
    user_name: str = Form(...),
    create_new_user: bool = Form(False)
):
    """Tag an unknown face with a user name"""
    if create_new_user:
        # This would create a new user in your social app
        new_user_id = str(uuid.uuid4())
        return {
            "message": f"Unknown face tagged as new user: {user_name}",
            "new_user_id": new_user_id,
            "face_id": face_id
        }
    else:
        return {
            "message": f"Unknown face tagged as existing user: {user_name}",
            "face_id": face_id
        }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "registered_users": len(registered_users),
        "processed_events": len(processing_results),
        "timestamp": datetime.now().isoformat()
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)