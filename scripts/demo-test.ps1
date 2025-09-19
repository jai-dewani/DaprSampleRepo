# Demo Script - Test the Dapr Microservices
# This script demonstrates the functionality of all three services

Write-Host "=== Dapr Microservices Demo Test Script ===" -ForegroundColor Green
Write-Host ""

# $baseUrl = "http://localhost"
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

Write-Host ""
Write-Host "3. Creating test orders..." -ForegroundColor Cyan

$orders = @(
    @{
        customer_id = "customer-123"
        items = @(
            @{ product_id = "laptop-001"; quantity = 1; price = 1299.99 },
            @{ product_id = "mouse-001"; quantity = 2; price = 29.99 }
        )
    },
    @{
        customer_id = "customer-456"
        items = @(
            @{ product_id = "keyboard-001"; quantity = 1; price = 89.99 },
            @{ product_id = "mouse-001"; quantity = 1; price = 29.99 }
        )
    }
)

$createdOrders = @()
foreach ($order in $orders) {
    $result = Invoke-DemoRequest "$orderServiceUrl/orders" -Method "POST" -Body $order
    if ($result) {
        Write-Host "  ✓ Created order: $($result.order_id) for customer $($result.customer_id)" -ForegroundColor Green
        $createdOrders += $result.order_id
    }
}

Write-Host ""
Write-Host "4. Waiting for events to process..." -ForegroundColor Yellow
Start-Sleep -Seconds 3

Write-Host ""
Write-Host "5. Checking notifications..." -ForegroundColor Cyan
$notifications = Invoke-DemoRequest "$notificationServiceUrl/notifications"
if ($notifications) {
    Write-Host "  Total notifications: $($notifications.total)" -ForegroundColor Green
    foreach ($notification in $notifications.notifications) {
        Write-Host "    - $($notification.type): $($notification.message)" -ForegroundColor White
    }
}

Write-Host ""
Write-Host "6. Checking inventory levels..." -ForegroundColor Cyan
foreach ($item in $inventoryItems) {
    $inventory = Invoke-DemoRequest "$inventoryServiceUrl/inventory/$($item.product_id)"
    if ($inventory) {
        Write-Host "  $($inventory.name): $($inventory.quantity) units remaining" -ForegroundColor White
    }
}

Write-Host ""
Write-Host "7. Updating order status..." -ForegroundColor Cyan
if ($createdOrders.Count -gt 0) {
    $orderId = $createdOrders[0]
    $statusUpdate = @{ status = "completed" }
    $result = Invoke-DemoRequest "$orderServiceUrl/orders/$orderId/status" -Method "PUT" -Body $statusUpdate
    if ($result) {
        Write-Host "  ✓ Updated order $orderId to completed status" -ForegroundColor Green
    }
}

Write-Host ""
Write-Host "=== Demo Complete! ===" -ForegroundColor Green
Write-Host "Check the service logs to see the pub/sub messages and state store operations." -ForegroundColor Yellow
Write-Host ""
Write-Host "API Endpoints to try:" -ForegroundColor Cyan
Write-Host "  GET  $orderServiceUrl/health" -ForegroundColor White
Write-Host "  POST $orderServiceUrl/orders" -ForegroundColor White
Write-Host "  GET  $inventoryServiceUrl/inventory/{product_id}" -ForegroundColor White
Write-Host "  POST $inventoryServiceUrl/inventory" -ForegroundColor White
Write-Host "  GET  $notificationServiceUrl/notifications" -ForegroundColor White
