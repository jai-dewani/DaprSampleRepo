# Demo Script - Test the Dapr Microservices
# This script demonstrates the functionality of all three services

Write-Host "=== Dapr Microservices Demo Test Script ===" -ForegroundColor Green
Write-Host ""

$orderServiceUrl = "http://localhost:5001"
$inventoryServiceUrl = "http://localhost:5002"
$notificationServiceUrl = "http://localhost:5003"

Write-Host "DEBUG: Order Service URL: $orderServiceUrl" -ForegroundColor Yellow
Write-Host "DEBUG: Inventory Service URL: $inventoryServiceUrl" -ForegroundColor Yellow
Write-Host "DEBUG: Notification Service URL: $notificationServiceUrl" -ForegroundColor Yellow

# Function to make HTTP requests
function Invoke-DemoRequest {
    param($Url, $Method = "GET", $Body = $null)

    # Add debugging
    Write-Host "DEBUG: Calling URL: $Url" -ForegroundColor Yellow
    
    try {
        if ($Body) {
            $response = Invoke-RestMethod -Uri $Url -Method $Method -Body ($Body | ConvertTo-Json) -ContentType "application/json"
        } else {
            $response = Invoke-RestMethod -Uri $Url -Method $Method
        }
        return $response
    } catch {
        Write-Host "Error calling $Url : $($_.Exception.Message)" -ForegroundColor Red
        return $null
    }
}

Write-Host "0. Cleaning up previous data..." -ForegroundColor Magenta
$clearResult = Invoke-DemoRequest "$inventoryServiceUrl/inventory" -Method "DELETE"
if ($clearResult) {
    Write-Host "  ✓ Cleared $($clearResult.cleared_items) existing inventory items" -ForegroundColor Green
} else {
    Write-Host "  ℹ No previous inventory data found" -ForegroundColor Gray
}

Write-Host ""
Write-Host "1. Checking service health..." -ForegroundColor Cyan
$orderHealth = Invoke-DemoRequest "$orderServiceUrl/health"
$inventoryHealth = Invoke-DemoRequest "$inventoryServiceUrl/health"
$notificationHealth = Invoke-DemoRequest "$notificationServiceUrl/health"

if ($orderHealth) { Write-Host "  ✓ Order Service: $($orderHealth.status)" -ForegroundColor Green }
if ($inventoryHealth) { Write-Host "  ✓ Inventory Service: $($inventoryHealth.status)" -ForegroundColor Green }
if ($notificationHealth) { Write-Host "  ✓ Notification Service: $($notificationHealth.status)" -ForegroundColor Green }

Write-Host ""
Write-Host "2. Adding inventory items..." -ForegroundColor Cyan

$inventoryItems = @(
    @{ product_id = "laptop-001"; quantity = 10; name = "Gaming Laptop"; price = 1299.99 },
    @{ product_id = "mouse-001"; quantity = 50; name = "Wireless Mouse"; price = 29.99 },
    @{ product_id = "keyboard-001"; quantity = 25; name = "Mechanical Keyboard"; price = 89.99 }
)

foreach ($item in $inventoryItems) {
    $result = Invoke-DemoRequest "$inventoryServiceUrl/inventory" -Method "POST" -Body $item
    if ($result) {
        Write-Host "  ✓ Added $($item.name): $($item.quantity) units" -ForegroundColor Green
    }
}

# ...rest of your existing demo script...

Write-Host ""
Write-Host "8. Demo cleanup (optional)..." -ForegroundColor Magenta
$cleanup = Read-Host "Do you want to clean up the demo data? (y/N)"
if ($cleanup -eq "y" -or $cleanup -eq "Y") {
    Write-Host "Cleaning up inventory..." -ForegroundColor Yellow
    $cleanupResult = Invoke-DemoRequest "$inventoryServiceUrl/inventory" -Method "DELETE"
    if ($cleanupResult) {
        Write-Host "  ✓ Cleaned up $($cleanupResult.cleared_items) inventory items" -ForegroundColor Green
    }
    
    Write-Host "Note: Orders and notifications are preserved for reference" -ForegroundColor Gray
}

Write-Host ""
Write-Host "=== Demo Complete! ===" -ForegroundColor Green
Write-Host "Check the service logs to see the pub/sub messages and state store operations." -ForegroundColor Yellow