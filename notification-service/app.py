from flask import Flask, request, jsonify
import json
import logging
import requests
from datetime import datetime

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

# Dapr sidecar endpoint
DAPR_HTTP_PORT = 3502
DAPR_URL = f"http://localhost:{DAPR_HTTP_PORT}"

# In-memory storage for notifications (in production, use a proper database)
notifications = []

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "service": "notification-service"})

@app.route('/notifications', methods=['GET'])
def get_notifications():
    """Get all notifications"""
    try:
        # In production, you'd implement pagination and filtering
        return jsonify({
            "notifications": notifications,
            "total": len(notifications)
        })
        
    except Exception as e:
        app.logger.error(f"Error retrieving notifications: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@app.route('/notifications', methods=['POST'])
def send_notification():
    """Send a custom notification"""
    try:
        notification_data = request.json
        
        required_fields = ['recipient', 'message', 'type']
        for field in required_fields:
            if field not in notification_data:
                return jsonify({"error": f"Missing required field: {field}"}), 400
        
        notification = {
            "id": len(notifications) + 1,
            "recipient": notification_data["recipient"],
            "message": notification_data["message"],
            "type": notification_data["type"],
            "sent_at": datetime.utcnow().isoformat(),
            "status": "sent"
        }
        
        notifications.append(notification)
        
        # Store notification in Dapr state store
        state_url = f"{DAPR_URL}/v1.0/state/redis-statestore"
        state_data = [{"key": f"notification:{notification['id']}", "value": notification}]
        
        response = requests.post(state_url, json=state_data)
        if response.status_code != 204:
            app.logger.error(f"Failed to save notification: {response.text}")
        
        app.logger.info(f"Notification sent to {notification['recipient']}: {notification['message']}")
        return jsonify(notification), 201
        
    except Exception as e:
        app.logger.error(f"Error sending notification: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

def create_notification(recipient, message, notification_type, related_data=None):
    """Helper function to create notifications"""
    notification = {
        "id": len(notifications) + 1,
        "recipient": recipient,
        "message": message,
        "type": notification_type,
        "sent_at": datetime.utcnow().isoformat(),
        "status": "sent",
        "related_data": related_data or {}
    }
    
    notifications.append(notification)
    
    # Store in state store
    try:
        state_url = f"{DAPR_URL}/v1.0/state/redis-statestore"
        state_data = [{"key": f"notification:{notification['id']}", "value": notification}]
        requests.post(state_url, json=state_data)
    except Exception as e:
        app.logger.error(f"Failed to save notification to state store: {str(e)}")
    
    return notification

@app.route('/dapr/subscribe', methods=['GET'])
def subscribe():
    """Dapr subscription endpoint"""
    subscriptions = [
        {
            "pubsubname": "redis-pubsub",
            "topic": "order-events",
            "route": "/handle-order-event"
        },
        {
            "pubsubname": "redis-pubsub",
            "topic": "inventory-events",
            "route": "/handle-inventory-event"
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
        order_id = actual_data.get("order_id")
        customer_id = actual_data.get("customer_id")
        
        if event_type == "order_created":
            message = f"Your order {order_id} has been created successfully! Total amount: ${actual_data.get('total_amount', 0):.2f}"
            create_notification(
                recipient=customer_id,
                message=message,
                notification_type="order_confirmation",
                related_data={"order_id": order_id, "total_amount": actual_data.get("total_amount")}
            )
            
        elif event_type == "order_status_updated":
            status = actual_data.get("status")
            message = f"Your order {order_id} status has been updated to: {status}"
            create_notification(
                recipient=customer_id,
                message=message,
                notification_type="order_update",
                related_data={"order_id": order_id, "status": status}
            )
        
        return "", 200
        
    except Exception as e:
        app.logger.error(f"Error handling order event: {str(e)}")
        return "", 500

@app.route('/handle-inventory-event', methods=['POST'])
def handle_inventory_event():
    """Handle inventory events from pub/sub"""
    try:
        event_data = request.json
        app.logger.info(f"Received inventory event: {event_data}")
        
        # Extract the actual event data from Dapr's CloudEvent format
        if 'data' in event_data:
            actual_data = event_data['data']
        else:
            actual_data = event_data
        
        event_type = actual_data.get("event_type")
        order_id = actual_data.get("order_id")
        customer_id = actual_data.get("customer_id", "unknown_customer")
        
        if event_type == "inventory_processed":
            inventory_status = actual_data.get("inventory_status", [])
            all_items_reserved = actual_data.get("all_items_reserved", False)
            
            if all_items_reserved:
                reserved_items = [f"{item['product_id']} ({item['reserved_quantity']} units)" 
                                for item in inventory_status if item["status"] == "reserved"]
                message = f"Great news! All items for order {order_id} have been reserved: {', '.join(reserved_items)}"
                notification_type = "inventory_reserved"
            else:
                # Find items that couldn't be reserved
                problem_items = []
                for item in inventory_status:
                    if item["status"] == "insufficient":
                        problem_items.append(f"{item['product_id']} (need more, only {item['available_quantity']} available)")
                    elif item["status"] == "reservation_failed":
                        problem_items.append(f"{item['product_id']} (reservation failed)")
                
                message = f"Order {order_id} has inventory issues: {', '.join(problem_items)}"
                notification_type = "inventory_insufficient"
            
            create_notification(
                recipient=customer_id,
                message=message,
                notification_type=notification_type,
                related_data={"order_id": order_id, "inventory_status": inventory_status}
            )
        
        return "", 200
        
    except Exception as e:
        app.logger.error(f"Error handling inventory event: {str(e)}")
        return "", 500

@app.route('/notifications/customer/<customer_id>', methods=['GET'])
def get_customer_notifications(customer_id):
    """Get notifications for a specific customer"""
    try:
        customer_notifications = [n for n in notifications if n["recipient"] == customer_id]
        return jsonify({
            "customer_id": customer_id,
            "notifications": customer_notifications,
            "total": len(customer_notifications)
        })
        
    except Exception as e:
        app.logger.error(f"Error retrieving customer notifications: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5003, debug=True)
