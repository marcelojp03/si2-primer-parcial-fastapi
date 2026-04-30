# SI2 1P FastAPI - Deploy to ECR
# Uso: .\scripts\deploy\deploy-to-ecr.ps1
# Uso con tag: .\scripts\deploy\deploy-to-ecr.ps1 -ImageTag v1.0.0

param(
    [string]$ImageTag = "latest"
)

# Variables ECR
$AWS_REGION     = "us-east-1"
$AWS_ACCOUNT_ID = "851725478821"
$ECR_REPO_NAME  = "si2-1p-fastapi"
$ECR_URI        = "$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPO_NAME"

# Directorio raiz del proyecto (dos niveles arriba de scripts/deploy/)
$PROJECT_ROOT = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "  SI2 1P FastAPI - Deploy ECR" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

# 1. Verificar Docker
Write-Host "[1/5] Verificando Docker..." -ForegroundColor Cyan
$dockerRunning = $false
try {
    docker ps > $null 2>&1
    if ($LASTEXITCODE -eq 0) { $dockerRunning = $true }
} catch {}

if (-not $dockerRunning) {
    Write-Host "Docker Desktop no esta corriendo. Iniciando..." -ForegroundColor Yellow
    Start-Process "Docker Desktop" -WindowStyle Hidden

    $timeout = 60
    $elapsed = 0
    while (-not $dockerRunning -and $elapsed -lt $timeout) {
        Start-Sleep -Seconds 5
        $elapsed += 5
        try {
            docker ps > $null 2>&1
            if ($LASTEXITCODE -eq 0) { $dockerRunning = $true; break }
        } catch {}
        Write-Host "." -NoNewline -ForegroundColor Gray
    }
    Write-Host ""

    if (-not $dockerRunning) {
        Write-Host "ERROR: Docker no pudo iniciarse. Abrelo manualmente y reintenta." -ForegroundColor Red
        exit 1
    }
}
Write-Host "OK: Docker listo" -ForegroundColor Green

# 2. Build imagen
Write-Host "`n[2/5] Construyendo imagen Docker..." -ForegroundColor Cyan
Write-Host "Contexto: $PROJECT_ROOT" -ForegroundColor Gray
docker build -t "${ECR_REPO_NAME}:${ImageTag}" $PROJECT_ROOT

if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Fallo el build de la imagen" -ForegroundColor Red
    exit 1
}
Write-Host "OK: Imagen construida -> ${ECR_REPO_NAME}:${ImageTag}" -ForegroundColor Green

# 3. Autenticar con ECR
Write-Host "`n[3/5] Autenticando con ECR ($AWS_REGION)..." -ForegroundColor Cyan
$loginPassword = aws ecr get-login-password --region $AWS_REGION
$loginPassword | docker login --username AWS --password-stdin $ECR_URI

if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Fallo la autenticacion con ECR" -ForegroundColor Red
    Write-Host "Verificar credenciales AWS: aws configure" -ForegroundColor Yellow
    exit 1
}
Write-Host "OK: Autenticado con ECR" -ForegroundColor Green

# 4. Etiquetar y subir
Write-Host "`n[4/5] Etiquetando imagen..." -ForegroundColor Cyan
docker tag "${ECR_REPO_NAME}:${ImageTag}" "${ECR_URI}:${ImageTag}"

if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Fallo al etiquetar la imagen" -ForegroundColor Red
    exit 1
}

Write-Host "Subiendo a ECR..." -ForegroundColor Cyan
Write-Host "URI: ${ECR_URI}:${ImageTag}" -ForegroundColor Gray
docker push "${ECR_URI}:${ImageTag}"

if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Fallo al subir la imagen" -ForegroundColor Red
    exit 1
}
Write-Host "OK: Imagen subida" -ForegroundColor Green

# 5. Resumen
Write-Host "`n[5/5] Completado!" -ForegroundColor Cyan
Write-Host "`n========================================" -ForegroundColor Green
Write-Host "  DEPLOYMENT EXITOSO" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host "ECR URI : ${ECR_URI}:${ImageTag}" -ForegroundColor Cyan
Write-Host "`nProximo paso: Desplegar en App Runner" -ForegroundColor Yellow
Write-Host "  1. Ve a AWS Console -> App Runner" -ForegroundColor White
Write-Host "  2. Selecciona 'Deploy' en el servicio si2-1p-fastapi" -ForegroundColor White
Write-Host "  3. Verifica variables de entorno (DATABASE_URL, OPENAI_API_KEY, etc.)" -ForegroundColor White
