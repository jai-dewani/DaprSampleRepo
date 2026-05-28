# Clear Inventory Script
# This script clears all inventory from the inventory service

Write-Host "=== Clear Inventory Script ===" -ForegroundColor Yellow
Write-Host ""

$inventoryServiceUrl = "http://localhost:5002"

# Function to make HTTP requests
function Invoke-ClearRequest {
    param($Url, $Method = "GET")

    Write-Host "DEBUG: Calling URL: $Url with method: $Method" -ForegroundColor Yellow
    
    try {
        $response = Invoke-RestMethod -Uri $Url -Method $Method
        return $response
    } catch {
        Write-Host "Error calling $Url : $($_.Exception.Message)" -ForegroundColor Red
        return $null
    }
}

# Check if inventory service is running
Write-Host "1. Checking inventory service health..." -ForegroundColor Cyan
$health = Invoke-ClearRequest "$inventoryServiceUrl/health"

if ($health) {
    Write-Host "  ✓ Inventory Service: $($health.status)" -ForegroundColor Green
} else {
    Write-Host "  ✗ Inventory Service is not responding!" -ForegroundColor Red
    Write-Host "  Make sure the inventory service is running on port 5002" -ForegroundColor Yellow
    exit 1
}

Write-Host ""
Write-Host "2. Listing current inventory before clearing..." -ForegroundColor Cyan
$currentInventory = Invoke-ClearRequest "$inventoryServiceUrl/inventory/list"

if ($currentInventory) {
    Write-Host "  Current inventory items: $($currentInventory.total_items)" -ForegroundColor White
    foreach ($item in $currentInventory.inventory_items) {
        Write-Host "    - $($item.name) ($($item.product_id)): $($item.quantity) units" -ForegroundColor White
    }
} else {
    Write-Host "  No inventory items found or error retrieving inventory" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "3. Clearing all inventory..." -ForegroundColor Cyan
$clearResult = Invoke-ClearRequest "$inventoryServiceUrl/inventory/clear" -Method "DELETE"

if ($clearResult) {
    Write-Host "  ✓ $($clearResult.message)" -ForegroundColor Green
    Write-Host "  Total items cleared: $($clearResult.total_cleared)" -ForegroundColor Green
    
    if ($clearResult.cleared_items -and $clearResult.cleared_items.Count -gt 0) {
        Write-Host "  Cleared items:" -ForegroundColor White
        foreach ($item in $clearResult.cleared_items) {
            Write-Host "    - $($item.name) ($($item.product_id)): $($item.quantity_cleared) units cleared" -ForegroundColor White
        }
    }
} else {
    Write-Host "  ✗ Failed to clear inventory!" -ForegroundColor Red
}

Write-Host ""
Write-Host "4. Verifying inventory is cleared..." -ForegroundColor Cyan
$verifyInventory = Invoke-ClearRequest "$inventoryServiceUrl/inventory/list"

if ($verifyInventory) {
    Write-Host "  Remaining inventory items: $($verifyInventory.total_items)" -ForegroundColor White
    if ($verifyInventory.total_items -eq 0) {
        Write-Host "  ✓ All inventory successfully cleared!" -ForegroundColor Green
    } else {
        Write-Host "  ⚠ Some items may still remain:" -ForegroundColor Yellow
        foreach ($item in $verifyInventory.inventory_items) {
            Write-Host "    - $($item.name) ($($item.product_id)): $($item.quantity) units" -ForegroundColor Yellow
        }
    }
}

Write-Host ""
Write-Host "=== Clear Inventory Complete! ===" -ForegroundColor Green
Write-Host ""
Write-Host "You can now run the demo test script to add fresh inventory:" -ForegroundColor Cyan
Write-Host "  .\scripts\demo-test.ps1" -ForegroundColor White
Write-Host ""
Write-Host "Or manually add inventory using:" -ForegroundColor Cyan
Write-Host "  POST $inventoryServiceUrl/inventory" -ForegroundColor White
Write-Host "  Body: {\"product_id\": \"example-001\", \"quantity\": 10, \"name\": \"Example Product\", \"price\": 99.99}" -ForegroundColor White
