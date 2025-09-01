// Script to download face-api.js models
const https = require('https');
const fs = require('fs');
const path = require('path');

const models = [
    'ssd_mobilenetv1_model-weights_manifest.json',
    'ssd_mobilenetv1_model-shard1',
    'face_landmark_68_model-weights_manifest.json',
    'face_landmark_68_model-shard1',
    'face_recognition_model-weights_manifest.json',
    'face_recognition_model-shard1',
    'face_recognition_model-shard2'
];

const baseUrl = 'https://raw.githubusercontent.com/justadudewhohacks/face-api.js/master/weights/';

async function downloadModel(filename) {
    return new Promise((resolve, reject) => {
        const url = baseUrl + filename;
        const filePath = path.join('models', filename);
        
        console.log(`Downloading ${filename}...`);
        
        const file = fs.createWriteStream(filePath);
        https.get(url, (response) => {
            response.pipe(file);
            file.on('finish', () => {
                file.close();
                console.log(`✓ Downloaded ${filename}`);
                resolve();
            });
        }).on('error', (err) => {
            fs.unlink(filePath, () => {}); // Delete the file on error
            reject(err);
        });
    });
}

async function downloadAllModels() {
    try {
        for (const model of models) {
            await downloadModel(model);
        }
        console.log('\n✅ All models downloaded successfully!');
        console.log('You can now run the face detection app.');
    } catch (error) {
        console.error('❌ Error downloading models:', error);
    }
}

downloadAllModels();