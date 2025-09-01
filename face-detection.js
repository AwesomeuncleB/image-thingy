class EventFaceDetection {
    constructor() {
        this.registeredUsers = new Map();
        this.isModelLoaded = false;
        this.initializeFaceAPI();
    }

    async initializeFaceAPI() {
        try {
            // Load face-api.js models
            await faceapi.nets.ssdMobilenetv1.loadFromUri('./models');
            await faceapi.nets.faceLandmark68Net.loadFromUri('./models');
            await faceapi.nets.faceRecognitionNet.loadFromUri('./models');
            
            this.isModelLoaded = true;
            this.showStatus('Face detection models loaded successfully!', 'success');
        } catch (error) {
            console.error('Error loading models:', error);
            this.showStatus('Error loading face detection models. Please check if models are available.', 'error');
        }
    }

    showStatus(message, type = 'loading') {
        const statusDiv = document.getElementById('processingStatus');
        statusDiv.innerHTML = `<div class="status ${type}">${message}</div>`;
    }

    async registerUser() {
        const userName = document.getElementById('userName').value.trim();
        const userPhotoInput = document.getElementById('userPhoto');
        
        if (!userName || !userPhotoInput.files[0]) {
            alert('Please enter a name and select a photo');
            return;
        }

        if (!this.isModelLoaded) {
            alert('Face detection models are still loading. Please wait.');
            return;
        }

        try {
            const file = userPhotoInput.files[0];
            const img = await this.loadImage(file);
            
            // Detect face and get descriptor
            const detection = await faceapi
                .detectSingleFace(img)
                .withFaceLandmarks()
                .withFaceDescriptor();

            if (!detection) {
                alert('No face detected in the image. Please try another photo.');
                return;
            }

            // Store user data
            const userData = {
                name: userName,
                descriptor: detection.descriptor,
                photo: URL.createObjectURL(file),
                id: Date.now().toString()
            };

            this.registeredUsers.set(userData.id, userData);
            this.displayRegisteredUsers();
            
            // Clear inputs
            document.getElementById('userName').value = '';
            document.getElementById('userPhoto').value = '';
            
            this.showStatus(`User ${userName} registered successfully!`, 'success');
        } catch (error) {
            console.error('Error registering user:', error);
            alert('Error registering user. Please try again.');
        }
    }

    displayRegisteredUsers() {
        const container = document.getElementById('registeredUsers');
        container.innerHTML = '';
        
        this.registeredUsers.forEach(user => {
            const userCard = document.createElement('div');
            userCard.className = 'user-card';
            userCard.innerHTML = `
                <img src="${user.photo}" alt="${user.name}">
                <div>${user.name}</div>
                <button onclick="faceDetector.removeUser('${user.id}')" style="margin-top: 10px; padding: 5px 10px; font-size: 12px;">Remove</button>
            `;
            container.appendChild(userCard);
        });
    }

    removeUser(userId) {
        this.registeredUsers.delete(userId);
        this.displayRegisteredUsers();
    }

    async processEventPhotos() {
        const eventPhotosInput = document.getElementById('eventPhotos');
        
        if (!eventPhotosInput.files.length) {
            alert('Please select event photos to process');
            return;
        }

        if (!this.isModelLoaded) {
            alert('Face detection models are still loading. Please wait.');
            return;
        }

        if (this.registeredUsers.size === 0) {
            alert('Please register at least one user before processing photos');
            return;
        }

        this.showStatus('Processing event photos...', 'loading');
        
        const results = {
            userPhotos: new Map(), // userId -> array of photos they appear in
            unrecognizedFaces: [],
            organizerPhotos: [] // photos for organizer folder
        };

        try {
            const files = Array.from(eventPhotosInput.files);
            
            for (let i = 0; i < files.length; i++) {
                const file = files[i];
                this.showStatus(`Processing photo ${i + 1} of ${files.length}...`, 'loading');
                
                const photoResult = await this.processPhoto(file);
                
                // Organize results
                photoResult.recognizedFaces.forEach(face => {
                    if (!results.userPhotos.has(face.userId)) {
                        results.userPhotos.set(face.userId, []);
                    }
                    results.userPhotos.get(face.userId).push({
                        photo: file,
                        photoUrl: URL.createObjectURL(file),
                        confidence: face.confidence,
                        faceBox: face.box
                    });
                });

                if (photoResult.unrecognizedFaces.length > 0) {
                    results.unrecognizedFaces.push(...photoResult.unrecognizedFaces.map(face => ({
                        photo: file,
                        photoUrl: URL.createObjectURL(file),
                        faceImage: face.faceImage,
                        box: face.box
                    })));
                }

                // Add to organizer folder if it has faces or if organizer allows all photos
                if (photoResult.recognizedFaces.length > 0 || photoResult.unrecognizedFaces.length > 0) {
                    results.organizerPhotos.push({
                        photo: file,
                        photoUrl: URL.createObjectURL(file),
                        totalFaces: photoResult.recognizedFaces.length + photoResult.unrecognizedFaces.length
                    });
                }
            }

            this.displayResults(results);
            this.showStatus(`Successfully processed ${files.length} photos!`, 'success');
            
        } catch (error) {
            console.error('Error processing photos:', error);
            this.showStatus('Error processing photos. Please try again.', 'error');
        }
    }

    async processPhoto(file) {
        const img = await this.loadImage(file);
        
        // Detect all faces in the image
        const detections = await faceapi
            .detectAllFaces(img)
            .withFaceLandmarks()
            .withFaceDescriptors();

        const recognizedFaces = [];
        const unrecognizedFaces = [];

        for (const detection of detections) {
            const match = this.findBestMatch(detection.descriptor);
            
            if (match.distance < 0.6) { // Threshold for face recognition
                recognizedFaces.push({
                    userId: match.userId,
                    userName: match.userName,
                    confidence: Math.round((1 - match.distance) * 100),
                    box: detection.detection.box
                });
            } else {
                // Extract face image for unrecognized faces
                const faceImage = await this.extractFaceImage(img, detection.detection.box);
                unrecognizedFaces.push({
                    faceImage: faceImage,
                    box: detection.detection.box
                });
            }
        }

        return { recognizedFaces, unrecognizedFaces };
    }

    findBestMatch(descriptor) {
        let bestMatch = { distance: 1, userId: null, userName: null };
        
        this.registeredUsers.forEach((user, userId) => {
            const distance = faceapi.euclideanDistance(descriptor, user.descriptor);
            if (distance < bestMatch.distance) {
                bestMatch = { distance, userId, userName: user.name };
            }
        });

        return bestMatch;
    }

    async extractFaceImage(img, box) {
        const canvas = document.createElement('canvas');
        const ctx = canvas.getContext('2d');
        
        canvas.width = box.width;
        canvas.height = box.height;
        
        ctx.drawImage(img, box.x, box.y, box.width, box.height, 0, 0, box.width, box.height);
        
        return canvas.toDataURL();
    }

    displayResults(results) {
        const resultsContainer = document.getElementById('results');
        const unrecognizedContainer = document.getElementById('unrecognizedFaces');
        
        resultsContainer.innerHTML = '';
        unrecognizedContainer.innerHTML = '';

        // Display user photos
        results.userPhotos.forEach((photos, userId) => {
            const user = this.registeredUsers.get(userId);
            if (!user) return;

            const userResult = document.createElement('div');
            userResult.className = 'photo-result';
            userResult.innerHTML = `
                <h3>${user.name} appears in ${photos.length} photo(s)</h3>
                <div class="detected-faces">
                    ${photos.map(photo => `
                        <div class="face-match">
                            <img src="${photo.photoUrl}" alt="Photo with ${user.name}">
                            <div>Confidence: ${photo.confidence}%</div>
                            <button onclick="faceDetector.downloadUserPhoto('${userId}', '${photo.photoUrl}')">Download</button>
                        </div>
                    `).join('')}
                </div>
            `;
            resultsContainer.appendChild(userResult);
        });

        // Display unrecognized faces
        results.unrecognizedFaces.forEach((face, index) => {
            const faceDiv = document.createElement('div');
            faceDiv.className = 'unrecognized-face';
            faceDiv.innerHTML = `
                <img src="${face.faceImage}" alt="Unrecognized face">
                <div>Unknown Person ${index + 1}</div>
                <button onclick="faceDetector.tagUnrecognizedFace(${index})">Tag Person</button>
            `;
            unrecognizedContainer.appendChild(faceDiv);
        });

        // Store results for API integration
        this.lastResults = results;
    }

    // Method to get results in format suitable for your social app API
    getResultsForAPI() {
        if (!this.lastResults) return null;

        return {
            userPhotos: Array.from(this.lastResults.userPhotos.entries()).map(([userId, photos]) => ({
                userId: userId,
                userName: this.registeredUsers.get(userId).name,
                photos: photos.map(photo => ({
                    photoBlob: photo.photo,
                    confidence: photo.confidence,
                    faceBox: photo.faceBox
                }))
            })),
            unrecognizedFaces: this.lastResults.unrecognizedFaces,
            organizerPhotos: this.lastResults.organizerPhotos
        };
    }

    async loadImage(file) {
        return new Promise((resolve) => {
            const img = new Image();
            img.onload = () => resolve(img);
            img.src = URL.createObjectURL(file);
        });
    }

    downloadUserPhoto(userId, photoUrl) {
        const user = this.registeredUsers.get(userId);
        const link = document.createElement('a');
        link.href = photoUrl;
        link.download = `${user.name}_event_photo_${Date.now()}.jpg`;
        link.click();
    }

    tagUnrecognizedFace(index) {
        const name = prompt('Enter the name for this person:');
        if (name) {
            // This could be integrated with your social app to create new user or tag existing user
            alert(`Face tagged as ${name}. This would be sent to your social app for processing.`);
        }
    }
}

// Initialize the face detection system
const faceDetector = new EventFaceDetection();

// Global functions for HTML onclick events
function registerUser() {
    faceDetector.registerUser();
}

function processEventPhotos() {
    faceDetector.processEventPhotos();
}