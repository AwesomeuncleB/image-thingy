"""
Integration module for connecting the Face Detection API with your social event app
"""

import asyncio
import aiohttp
from typing import List, Dict, Any, Optional
import json
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class SocialAppIntegration:
    """Integration class for your social event app"""
    
    def __init__(self, social_app_base_url: str, social_app_api_key: str, 
                 face_detection_url: str = "http://localhost:8000"):
        self.social_app_url = social_app_base_url.rstrip('/')
        self.face_detection_url = face_detection_url.rstrip('/')
        self.api_key = social_app_api_key
        
        self.headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
    
    async def sync_event_users(self, event_id: str) -> Dict[str, Any]:
        """Sync users from social app to face detection API"""
        async with aiohttp.ClientSession() as session:
            # 1. Get users from your social app
            social_users = await self._get_social_app_users(session, event_id)
            
            # 2. Register users in face detection API
            registered_count = 0
            failed_registrations = []
            
            for user in social_users:
                try:
                    if user.get('profile_photo_url'):
                        success = await self._register_user_in_face_api(
                            session, user['id'], user['name'], user['profile_photo_url']
                        )
                        if success:
                            registered_count += 1
                        else:
                            failed_registrations.append(user['id'])
                except Exception as e:
                    logger.error(f"Failed to register user {user['id']}: {e}")
                    failed_registrations.append(user['id'])
            
            return {
                'total_users': len(social_users),
                'registered_count': registered_count,
                'failed_registrations': failed_registrations
            }
    
    async def process_event_photos_workflow(self, event_id: str, photo_urls: List[str]) -> Dict[str, Any]:
        """Complete workflow for processing event photos"""
        async with aiohttp.ClientSession() as session:
            # 1. Download photos from your social app
            photo_files = await self._download_photos(session, photo_urls)
            
            # 2. Process photos with face detection API
            processing_results = await self._process_photos_with_face_api(
                session, event_id, photo_files
            )
            
            # 3. Upload results back to social app
            upload_results = await self._upload_results_to_social_app(
                session, event_id, processing_results
            )
            
            return {
                'event_id': event_id,
                'processed_photos': len(photo_files),
                'processing_results': processing_results,
                'upload_results': upload_results,
                'completed_at': datetime.now().isoformat()
            }
    
    async def _get_social_app_users(self, session: aiohttp.ClientSession, event_id: str) -> List[Dict]:
        """Get users from your social app"""
        url = f"{self.social_app_url}/api/events/{event_id}/attendees"
        
        async with session.get(url, headers=self.headers) as response:
            if response.status == 200:
                data = await response.json()
                return data.get('attendees', [])
            else:
                logger.error(f"Failed to get users from social app: {response.status}")
                return []
    
    async def _register_user_in_face_api(self, session: aiohttp.ClientSession, 
                                       user_id: str, name: str, photo_url: str) -> bool:
        """Register user in face detection API"""
        try:
            # Download user photo
            async with session.get(photo_url) as photo_response:
                if photo_response.status != 200:
                    return False
                
                photo_data = await photo_response.read()
            
            # Register in face API
            data = aiohttp.FormData()
            data.add_field('name', name)
            data.add_field('user_id', user_id)
            data.add_field('photo', photo_data, filename=f'{user_id}.jpg', content_type='image/jpeg')
            
            url = f"{self.face_detection_url}/users/register"
            async with session.post(url, data=data) as response:
                return response.status == 200
                
        except Exception as e:
            logger.error(f"Error registering user {user_id}: {e}")
            return False
    
    async def _download_photos(self, session: aiohttp.ClientSession, photo_urls: List[str]) -> List[bytes]:
        """Download photos from URLs"""
        photo_files = []
        
        for url in photo_urls:
            try:
                async with session.get(url) as response:
                    if response.status == 200:
                        photo_data = await response.read()
                        photo_files.append(photo_data)
            except Exception as e:
                logger.error(f"Failed to download photo {url}: {e}")
        
        return photo_files
    
    async def _process_photos_with_face_api(self, session: aiohttp.ClientSession, 
                                          event_id: str, photo_files: List[bytes]) -> Dict:
        """Process photos with face detection API"""
        data = aiohttp.FormData()
        
        for i, photo_data in enumerate(photo_files):
            data.add_field('photos', photo_data, filename=f'photo_{i}.jpg', content_type='image/jpeg')
        
        url = f"{self.face_detection_url}/events/{event_id}/process-photos"
        
        async with session.post(url, data=data) as response:
            if response.status == 200:
                return await response.json()
            else:
                logger.error(f"Face detection processing failed: {response.status}")
                return {}
    
    async def _upload_results_to_social_app(self, session: aiohttp.ClientSession, 
                                          event_id: str, results: Dict) -> Dict:
        """Upload processing results to your social app"""
        # 1. Add photos to user accounts
        user_photo_results = []
        for user_id, photos in results.get('user_photos', {}).items():
            for photo in photos:
                result = await self._add_photo_to_user_account(
                    session, event_id, user_id, photo
                )
                user_photo_results.append(result)
        
        # 2. Create organizer folder
        organizer_result = await self._create_organizer_folder(
            session, event_id, results.get('organizer_photos', [])
        )
        
        # 3. Submit unrecognized faces for review
        unrecognized_result = await self._submit_unrecognized_faces(
            session, event_id, results.get('unrecognized_faces', [])
        )
        
        return {
            'user_photos_uploaded': len(user_photo_results),
            'organizer_folder_created': organizer_result,
            'unrecognized_faces_submitted': unrecognized_result
        }
    
    async def _add_photo_to_user_account(self, session: aiohttp.ClientSession, 
                                       event_id: str, user_id: str, photo_data: Dict) -> bool:
        """Add photo to user's account in social app"""
        url = f"{self.social_app_url}/api/users/{user_id}/photos"
        
        payload = {
            'event_id': event_id,
            'photo_id': photo_data['photo_id'],
            'confidence': photo_data['confidence'],
            'bounding_box': photo_data['bounding_box'],
            'added_at': datetime.now().isoformat()
        }
        
        async with session.post(url, json=payload, headers=self.headers) as response:
            return response.status == 200
    
    async def _create_organizer_folder(self, session: aiohttp.ClientSession, 
                                     event_id: str, organizer_photos: List[Dict]) -> bool:
        """Create organizer folder in social app"""
        url = f"{self.social_app_url}/api/events/{event_id}/organizer-folder"
        
        payload = {
            'photos': organizer_photos,
            'created_at': datetime.now().isoformat()
        }
        
        async with session.post(url, json=payload, headers=self.headers) as response:
            return response.status == 200
    
    async def _submit_unrecognized_faces(self, session: aiohttp.ClientSession, 
                                       event_id: str, unrecognized_faces: List[Dict]) -> bool:
        """Submit unrecognized faces for manual review"""
        url = f"{self.social_app_url}/api/events/{event_id}/unrecognized-faces"
        
        payload = {
            'faces': unrecognized_faces,
            'submitted_at': datetime.now().isoformat()
        }
        
        async with session.post(url, json=payload, headers=self.headers) as response:
            return response.status == 200

# Example usage
async def main():
    """Example of how to use the integration"""
    integration = SocialAppIntegration(
        social_app_base_url="https://your-social-app.com",
        social_app_api_key="your-api-key",
        face_detection_url="http://localhost:8000"
    )
    
    event_id = "event_123"
    
    # 1. Sync users from social app
    sync_result = await integration.sync_event_users(event_id)
    print(f"User sync result: {sync_result}")
    
    # 2. Process event photos
    photo_urls = [
        "https://your-social-app.com/photos/event1.jpg",
        "https://your-social-app.com/photos/event2.jpg"
    ]
    
    workflow_result = await integration.process_event_photos_workflow(event_id, photo_urls)
    print(f"Workflow result: {workflow_result}")

if __name__ == "__main__":
    asyncio.run(main())