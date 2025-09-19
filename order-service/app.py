from flask import Flask, request, jsonify
import json
import uuid
from datetime import datetime
import requests
import logging

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

# Dapr sidecar endpoint
DAPR_HTTP_PORT = 3500
DAPR_URL = f"http://localhost:{DAPR_HTTP_PORT}"

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "service": "order-service"})

@app.route('/orders', methods=['POST'])
def create_order():
    """Create a new order and publish event"""
    try:
        order_data = request.json
        
        # Validate required fields
        required_fields = ['customer_id', 'items']
        for field in required_fields:
            if field not in order_data:
                return jsonify({"error": f"Missing required field: {field}"}), 400
        
        # Generate order ID and timestamp
        order_id = str(uuid.uuid4())
        order = {
            "order_id": order_id,
            "customer_id": order_data["customer_id"],
            "items": order_data["items"],
            "status": "pending",
            "created_at": datetime.utcnow().isoformat(),
            "total_amount": sum(item.get("price", 0) * item.get("quantity", 1) for item in order_data["items"])
        }
        
        # Save order to state store
        state_url = f"{DAPR_URL}/v1.0/state/redis-statestore"
        state_data = [{"key": f"order:{order_id}", "value": order}]
        
        response = requests.post(state_url, json=state_data)
        if response.status_code != 204:
            app.logger.error(f"Failed to save order to state store: {response.text}")
            return jsonify({"error": "Failed to save order"}), 500
        
        # Publish order created event
        event_data = {
            "order_id": order_id,
            "customer_id": order["customer_id"],
            "items": order["items"],
            "total_amount": order["total_amount"],
            "event_type": "order_created"
        }
        
        pubsub_url = f"{DAPR_URL}/v1.0/publish/redis-pubsub/order-events"
        publish_response = requests.post(pubsub_url, json=event_data)
        
        if publish_response.status_code != 204:
            app.logger.error(f"Failed to publish event: {publish_response.text}")
        
        app.logger.info(f"Order created: {order_id}")
        return jsonify(order), 201
        
    except Exception as e:
        app.logger.error(f"Error creating order: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@app.route('/orders/<order_id>', methods=['GET'])
def get_order(order_id):
    """Get order by ID"""
    try:
        state_url = f"{DAPR_URL}/v1.0/state/redis-statestore/order:{order_id}"
        response = requests.get(state_url)
        
        if response.status_code == 204:  # No content means key doesn't exist
            return jsonify({"error": "Order not found"}), 404
        
        if response.status_code != 200:
            return jsonify({"error": "Failed to retrieve order"}), 500
        
        order = response.json()
        return jsonify(order)
        
    except Exception as e:
        app.logger.error(f"Error retrieving order: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@app.route('/orders/<order_id>/status', methods=['PUT'])
def update_order_status(order_id):
    """Update order status"""
    try:
        status_data = request.json
        new_status = status_data.get('status')
        
        if not new_status:
            return jsonify({"error": "Status is required"}), 400
        
        # Get current order
        state_url = f"{DAPR_URL}/v1.0/state/redis-statestore/order:{order_id}"
        response = requests.get(state_url)
        
        if response.status_code == 204:
            return jsonify({"error": "Order not found"}), 404
        
        order = response.json()
        order["status"] = new_status
        order["updated_at"] = datetime.utcnow().isoformat()
        
        # Update order in state store
        state_data = [{"key": f"order:{order_id}", "value": order}]
        update_response = requests.post(state_url.replace(f"/order:{order_id}", ""), json=state_data)
        
        if update_response.status_code != 204:
            return jsonify({"error": "Failed to update order"}), 500
        
        # Publish status update event
        event_data = {
            "order_id": order_id,
            "status": new_status,
            "event_type": "order_status_updated"
        }
        
        pubsub_url = f"{DAPR_URL}/v1.0/publish/redis-pubsub/order-events"
        requests.post(pubsub_url, json=event_data)
        
        app.logger.info(f"Order {order_id} status updated to {new_status}")
        return jsonify(order)
        
    except Exception as e:
        app.logger.error(f"Error updating order status: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@app.route('/orders', methods=['GET'])
def list_orders():
    """List all orders (simple implementation)"""
    try:
        # Note: In a production system, you'd implement proper pagination and filtering
        # This is a simplified version for demo purposes
        return jsonify({"message": "Use GET /orders/{order_id} to retrieve specific orders"}), 200
        
    except Exception as e:
        app.logger.error(f"Error listing orders: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)
