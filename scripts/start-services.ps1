# Dapr Microservices Demo - Start Script
# This script starts all three services with Dapr sidecars

Write-Host "Starting Dapr Microservices Demo..." -ForegroundColor Green

# Check if Dapr is installed
if (!(Get-Command "dapr" -ErrorAction SilentlyContinue)) {
    Write-Host "Dapr CLI not found. Please install Dapr first." -ForegroundColor Red
    Write-Host "Visit: https://docs.dapr.io/getting-started/install-dapr-cli/" -ForegroundColor Yellow
    exit 1
}

# Check if Redis is running
Write-Host "Checking Redis connection..." -ForegroundColor Yellow
try {
    $redis = Test-NetConnection -ComputerName localhost -Port 6379 -WarningAction SilentlyContinue
    if (!$redis.TcpTestSucceeded) {
        Write-Host "Redis is not running. Starting Redis with Docker..." -ForegroundColor Yellow
        docker run -d --name redis-dapr -p 6379:6379 redis:7-alpine
        Start-Sleep -Seconds 5
    }
} catch {
    Write-Host "Starting Redis with Docker..." -ForegroundColor Yellow
    docker run -d --name redis-dapr -p 6379:6379 redis:7-alpine
    Start-Sleep -Seconds 5
}

# Set the components path
$componentsPath = Join-Path $PSScriptRoot "..\dapr-components"

Write-Host "Starting Order Service..." -ForegroundColor Cyan
Start-Process PowerShell -ArgumentList "-NoExit", "-Command", "cd '$PSScriptRoot\..\order-service'; dapr run --app-id order-service --app-port 5001 --dapr-http-port 3500 --components-path '$componentsPath' -- python app.py"

Start-Sleep -Seconds 3

Write-Host "Starting Inventory Service..." -ForegroundColor Cyan
Start-Process PowerShell -ArgumentList "-NoExit", "-Command", "cd '$PSScriptRoot\..\inventory-service'; dapr run --app-id inventory-service --app-port 5002 --dapr-http-port 3501 --components-path '$componentsPath' -- python app.py"

Start-Sleep -Seconds 3

Write-Host "Starting Notification Service..." -ForegroundColor Cyan
Start-Process PowerShell -ArgumentList "-NoExit", "-Command", "cd '$PSScriptRoot\..\notification-service'; dapr run --app-id notification-service --app-port 5003 --dapr-http-port 3502 --components-path '$componentsPath' -- python app.py"

Write-Host ""
Write-Host "All services are starting up!" -ForegroundColor Green
Write-Host "Service URLs:" -ForegroundColor Yellow
Write-Host "  Order Service:        http://localhost:5001" -ForegroundColor White
Write-Host "  Inventory Service:    http://localhost:5002" -ForegroundColor White
Write-Host "  Notification Service: http://localhost:5003" -ForegroundColor White
Write-Host ""
Write-Host "Dapr Dashboard (optional): dapr dashboard" -ForegroundColor Cyan
Write-Host "To stop all services, run: .\stop-services.ps1" -ForegroundColor Cyan
