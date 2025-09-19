from flask import Flask, request, jsonify
import json
import logging
import requests
from datetime import datetime

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

# Dapr sidecar endpoint
DAPR_HTTP_PORT = 3501
DAPR_URL = f"http://localhost:{DAPR_HTTP_PORT}"

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "service": "inventory-service"})

@app.route('/inventory', methods=['POST'])
def add_inventory():
    """Add inventory items"""
    try:
        inventory_data = request.json
        
        # Validate required fields
        required_fields = ['product_id', 'quantity']
        for field in required_fields:
            if field not in inventory_data:
                return jsonify({"error": f"Missing required field: {field}"}), 400
        
        product_id = inventory_data["product_id"]
        quantity = inventory_data["quantity"]
        
        # Get current inventory
        current_inventory = get_inventory_item(product_id)
        if current_inventory:
            new_quantity = current_inventory["quantity"] + quantity
        else:
            new_quantity = quantity
        
        # Create inventory record
        inventory_item = {
            "product_id": product_id,
            "quantity": new_quantity,
            "last_updated": datetime.utcnow().isoformat(),
            "name": inventory_data.get("name", f"Product {product_id}"),
            "price": inventory_data.get("price", 0.0)
        }
        
        # Save to state store
        state_url = f"{DAPR_URL}/v1.0/state/redis-statestore"
        state_data = [{"key": f"inventory:{product_id}", "value": inventory_item}]
        
        response = requests.post(state_url, json=state_data)
        if response.status_code != 204:
            app.logger.error(f"Failed to save inventory: {response.text}")
            return jsonify({"error": "Failed to save inventory"}), 500
        
        app.logger.info(f"Inventory updated for product {product_id}: {new_quantity}")
        return jsonify(inventory_item), 201
        
    except Exception as e:
        app.logger.error(f"Error adding inventory: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

def get_inventory_item(product_id):
    """Helper function to get inventory item"""
    try:
        state_url = f"{DAPR_URL}/v1.0/state/redis-statestore/inventory:{product_id}"
        response = requests.get(state_url)
        
        if response.status_code == 204:  # No content means key doesn't exist
            return None
        
        if response.status_code == 200:
            return response.json()
        
        return None
    except Exception as e:
        app.logger.error(f"Error getting inventory item: {str(e)}")
        return None

@app.route('/inventory/<product_id>', methods=['GET'])
def get_inventory(product_id):
    """Get inventory for a specific product"""
    try:
        inventory_item = get_inventory_item(product_id)
        
        if not inventory_item:
            return jsonify({"error": "Product not found"}), 404
        
        return jsonify(inventory_item)
        
    except Exception as e:
        app.logger.error(f"Error retrieving inventory: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@app.route('/inventory/<product_id>/reserve', methods=['POST'])
def reserve_inventory(product_id):
    """Reserve inventory for an order"""
    try:
        reservation_data = request.json
        quantity_to_reserve = reservation_data.get("quantity", 0)
        order_id = reservation_data.get("order_id")
        
        if quantity_to_reserve <= 0:
            return jsonify({"error": "Invalid quantity"}), 400
        
        if not order_id:
            return jsonify({"error": "Order ID is required"}), 400
        
        # Get current inventory
        inventory_item = get_inventory_item(product_id)
        
        if not inventory_item:
            return jsonify({"error": "Product not found"}), 404
        
        if inventory_item["quantity"] < quantity_to_reserve:
            return jsonify({"error": "Insufficient inventory", "available": inventory_item["quantity"]}), 400
        
        # Update inventory
        inventory_item["quantity"] -= quantity_to_reserve
        inventory_item["last_updated"] = datetime.utcnow().isoformat()
        
        # Save updated inventory
        state_url = f"{DAPR_URL}/v1.0/state/redis-statestore"
        state_data = [{"key": f"inventory:{product_id}", "value": inventory_item}]
        
        response = requests.post(state_url, json=state_data)
        if response.status_code != 204:
            return jsonify({"error": "Failed to reserve inventory"}), 500
        
        # Create reservation record
        reservation = {
            "product_id": product_id,
            "order_id": order_id,
            "quantity": quantity_to_reserve,
            "reserved_at": datetime.utcnow().isoformat()
        }
        
        reservation_data = [{"key": f"reservation:{order_id}:{product_id}", "value": reservation}]
        requests.post(state_url, json=reservation_data)
        
        app.logger.info(f"Reserved {quantity_to_reserve} units of {product_id} for order {order_id}")
        return jsonify({
            "message": "Inventory reserved successfully",
            "reservation": reservation,
            "remaining_inventory": inventory_item["quantity"]
        })
        
    except Exception as e:
        app.logger.error(f"Error reserving inventory: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@app.route('/dapr/subscribe', methods=['GET'])
def subscribe():
    """Dapr subscription endpoint"""
    subscriptions = [
        {
            "pubsubname": "redis-pubsub",
            "topic": "order-events",
            "route": "/handle-order-event"
        }
    ]
    return json.dumps(subscriptions)

@app.route('/handle-order-event', methods=['POST'])
def handle_order_event():
    """Handle order events from pub/sub"""
    try:
        event_data = request.json
        app.logger.info(f"Received order event: {event_data}")
        
        # Extract the actual event data from Dapr's CloudEvent format
        if 'data' in event_data:
            actual_data = event_data['data']
        else:
            actual_data = event_data
        
        event_type = actual_data.get("event_type")
        
        if event_type == "order_created":
            # Process order items and check inventory
            order_id = actual_data.get("order_id")
            items = actual_data.get("items", [])
            
            inventory_status = []
            for item in items:
                product_id = item.get("product_id")
                quantity = item.get("quantity", 1)
                
                inventory_item = get_inventory_item(product_id)
                
                if inventory_item and inventory_item["quantity"] >= quantity:
                    inventory_status.append({
                        "product_id": product_id,
                        "status": "available",
                        "available_quantity": inventory_item["quantity"]
                    })
                else:
                    inventory_status.append({
                        "product_id": product_id,
                        "status": "insufficient",
                        "available_quantity": inventory_item["quantity"] if inventory_item else 0
                    })
            
            # Publish inventory check result
            inventory_event = {
                "order_id": order_id,
                "inventory_status": inventory_status,
                "event_type": "inventory_checked"
            }
            
            pubsub_url = f"{DAPR_URL}/v1.0/publish/redis-pubsub/inventory-events"
            requests.post(pubsub_url, json=inventory_event)
            
            app.logger.info(f"Inventory check completed for order {order_id}")
        
        # Return empty response with 200 status for successful processing
        return '', 200
        
    except Exception as e:
        app.logger.error(f"Error handling order event: {str(e)}")
        # Return 500 for retriable errors
        return '', 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002, debug=True)
