# Dapr Microservices Demo - Stop Script
# This script stops all Dapr services and cleans up

Write-Host "Stopping Dapr Microservices Demo..." -ForegroundColor Red

# Stop Dapr services
Write-Host "Stopping Dapr applications..." -ForegroundColor Yellow
dapr stop --app-id order-service
dapr stop --app-id inventory-service  
dapr stop --app-id notification-service

# Stop Redis container if it was started by our script
Write-Host "Stopping Redis container..." -ForegroundColor Yellow
docker stop redis-dapr 2>$null
docker rm redis-dapr 2>$null

Write-Host "All services stopped!" -ForegroundColor Green
