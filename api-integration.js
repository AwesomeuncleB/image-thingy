// API Integration helper for connecting to your social event app
class SocialEventAPI {
    constructor(baseUrl, apiKey) {
        this.baseUrl = baseUrl;
        this.apiKey = apiKey;
    }

    // Upload processed face detection results to your social app
    async uploadEventResults(eventId, results) {
        const payload = {
            eventId: eventId,
            processedAt: new Date().toISOString(),
            userPhotos: results.userPhotos,
            unrecognizedFaces: results.unrecognizedFaces,
            organizerPhotos: results.organizerPhotos,
            totalPhotosProcessed: results.organizerPhotos.length
        };

        try {
            const response = await fetch(`${this.baseUrl}/events/${eventId}/face-detection`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${this.apiKey}`
                },
                body: JSON.stringify(payload)
            });

            if (!response.ok) {
                throw new Error(`API Error: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error('Error uploading results:', error);
            throw error;
        }
    }

    // Get registered users from your social app for an event
    async getEventUsers(eventId) {
        try {
            const response = await fetch(`${this.baseUrl}/events/${eventId}/users`, {
                headers: {
                    'Authorization': `Bearer ${this.apiKey}`
                }
            });

            if (!response.ok) {
                throw new Error(`API Error: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error('Error fetching event users:', error);
            throw error;
        }
    }

    // Upload a photo to a user's account
    async addPhotoToUser(userId, photoBlob, metadata) {
        const formData = new FormData();
        formData.append('photo', photoBlob);
        formData.append('metadata', JSON.stringify(metadata));

        try {
            const response = await fetch(`${this.baseUrl}/users/${userId}/photos`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${this.apiKey}`
                },
                body: formData
            });

            if (!response.ok) {
                throw new Error(`API Error: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error('Error uploading photo to user:', error);
            throw error;
        }
    }

    // Create organizer folder with event photos
    async createOrganizerFolder(eventId, photos) {
        const formData = new FormData();
        
        photos.forEach((photo, index) => {
            formData.append(`photos`, photo.photo);
            formData.append(`metadata_${index}`, JSON.stringify({
                totalFaces: photo.totalFaces,
                uploadedAt: new Date().toISOString()
            }));
        });

        try {
            const response = await fetch(`${this.baseUrl}/events/${eventId}/organizer-photos`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${this.apiKey}`
                },
                body: formData
            });

            if (!response.ok) {
                throw new Error(`API Error: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error('Error creating organizer folder:', error);
            throw error;
        }
    }

    // Submit unrecognized faces for manual tagging
    async submitUnrecognizedFaces(eventId, unrecognizedFaces) {
        const formData = new FormData();
        
        unrecognizedFaces.forEach((face, index) => {
            // Convert face image data URL to blob
            const blob = this.dataURLToBlob(face.faceImage);
            formData.append(`faces`, blob, `unknown_face_${index}.jpg`);
            formData.append(`metadata_${index}`, JSON.stringify({
                originalPhoto: face.photo.name,
                boundingBox: face.box,
                detectedAt: new Date().toISOString()
            }));
        });

        try {
            const response = await fetch(`${this.baseUrl}/events/${eventId}/unrecognized-faces`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${this.apiKey}`
                },
                body: formData
            });

            if (!response.ok) {
                throw new Error(`API Error: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error('Error submitting unrecognized faces:', error);
            throw error;
        }
    }

    // Helper method to convert data URL to blob
    dataURLToBlob(dataURL) {
        const arr = dataURL.split(',');
        const mime = arr[0].match(/:(.*?);/)[1];
        const bstr = atob(arr[1]);
        let n = bstr.length;
        const u8arr = new Uint8Array(n);
        while (n--) {
            u8arr[n] = bstr.charCodeAt(n);
        }
        return new Blob([u8arr], { type: mime });
    }
}

// Enhanced EventFaceDetection class with API integration
class EventFaceDetectionWithAPI extends EventFaceDetection {
    constructor(apiConfig) {
        super();
        this.api = apiConfig ? new SocialEventAPI(apiConfig.baseUrl, apiConfig.apiKey) : null;
        this.currentEventId = null;
    }

    setEventId(eventId) {
        this.currentEventId = eventId;
    }

    setAPIConfig(baseUrl, apiKey) {
        this.api = new SocialEventAPI(baseUrl, apiKey);
    }

    // Load users from your social app for the current event
    async loadEventUsers() {
        if (!this.api || !this.currentEventId) {
            console.warn('API not configured or event ID not set');
            return;
        }

        try {
            this.showStatus('Loading event users from your app...', 'loading');
            const users = await this.api.getEventUsers(this.currentEventId);
            
            // Convert API users to our format
            for (const user of users) {
                if (user.profilePhoto) {
                    // Load user photo and extract face descriptor
                    const img = await this.loadImageFromUrl(user.profilePhoto);
                    const detection = await faceapi
                        .detectSingleFace(img)
                        .withFaceLandmarks()
                        .withFaceDescriptor();

                    if (detection) {
                        const userData = {
                            name: user.name,
                            descriptor: detection.descriptor,
                            photo: user.profilePhoto,
                            id: user.id,
                            fromAPI: true
                        };
                        this.registeredUsers.set(userData.id, userData);
                    }
                }
            }

            this.displayRegisteredUsers();
            this.showStatus(`Loaded ${users.length} users from event`, 'success');
        } catch (error) {
            console.error('Error loading event users:', error);
            this.showStatus('Error loading event users', 'error');
        }
    }

    // Upload results to your social app
    async uploadToSocialApp() {
        if (!this.api || !this.currentEventId || !this.lastResults) {
            alert('API not configured, event ID not set, or no results to upload');
            return;
        }

        try {
            this.showStatus('Uploading results to your social app...', 'loading');

            // Upload photos to individual user accounts
            for (const [userId, photos] of this.lastResults.userPhotos) {
                for (const photo of photos) {
                    await this.api.addPhotoToUser(userId, photo.photo, {
                        eventId: this.currentEventId,
                        confidence: photo.confidence,
                        faceBox: photo.faceBox,
                        detectedAt: new Date().toISOString()
                    });
                }
            }

            // Create organizer folder
            if (this.lastResults.organizerPhotos.length > 0) {
                await this.api.createOrganizerFolder(this.currentEventId, this.lastResults.organizerPhotos);
            }

            // Submit unrecognized faces for manual review
            if (this.lastResults.unrecognizedFaces.length > 0) {
                await this.api.submitUnrecognizedFaces(this.currentEventId, this.lastResults.unrecognizedFaces);
            }

            // Upload complete results
            await this.api.uploadEventResults(this.currentEventId, this.getResultsForAPI());

            this.showStatus('Successfully uploaded all results to your social app!', 'success');
        } catch (error) {
            console.error('Error uploading to social app:', error);
            this.showStatus('Error uploading to social app', 'error');
        }
    }

    async loadImageFromUrl(url) {
        return new Promise((resolve, reject) => {
            const img = new Image();
            img.crossOrigin = 'anonymous';
            img.onload = () => resolve(img);
            img.onerror = reject;
            img.src = url;
        });
    }
}

// Example usage configuration
const API_CONFIG = {
    baseUrl: 'https://your-social-app-api.com/api/v1', // Replace with your API URL
    apiKey: 'your-api-key-here' // Replace with your API key
};

// Initialize with API integration
const faceDetectorWithAPI = new EventFaceDetectionWithAPI(API_CONFIG);

// Additional functions for API integration
function setEventId() {
    const eventId = prompt('Enter Event ID:');
    if (eventId) {
        faceDetectorWithAPI.setEventId(eventId);
        document.getElementById('processingStatus').innerHTML = 
            `<div class="status success">Event ID set to: ${eventId}</div>`;
    }
}

function loadEventUsers() {
    faceDetectorWithAPI.loadEventUsers();
}

function uploadToSocialApp() {
    faceDetectorWithAPI.uploadToSocialApp();
}