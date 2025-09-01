# PowerShell script to download face-api.js models
$baseUrl = "https://raw.githubusercontent.com/justadudewhohacks/face-api.js/master/weights/"
$models = @(
    "ssd_mobilenetv1_model-weights_manifest.json",
    "ssd_mobilenetv1_model-shard1",
    "face_landmark_68_model-weights_manifest.json", 
    "face_landmark_68_model-shard1",
    "face_recognition_model-weights_manifest.json",
    "face_recognition_model-shard1",
    "face_recognition_model-shard2"
)

Write-Host "Downloading face-api.js models..." -ForegroundColor Green

foreach ($model in $models) {
    $url = $baseUrl + $model
    $output = "models\" + $model
    
    Write-Host "Downloading $model..." -ForegroundColor Yellow
    
    try {
        Invoke-WebRequest -Uri $url -OutFile $output
        Write-Host "✓ Downloaded $model" -ForegroundColor Green
    }
    catch {
        Write-Host "❌ Failed to download $model" -ForegroundColor Red
        Write-Host $_.Exception.Message
    }
}

Write-Host "`n✅ Model download complete!" -ForegroundColor Green
Write-Host "You can now open index.html in your browser to use the face detection app." -ForegroundColor Cyan