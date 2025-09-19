# Dapr Microservices Demo

A comprehensive demonstration of Dapr (Distributed Application Runtime) featuring three Python microservices that showcase pub/sub messaging and state management using Redis.

## Architecture Overview

This demo consists of three microservices:

1. **Order Service** (Port 5001) - Handles order creation and management
2. **Inventory Service** (Port 5002) - Manages product inventory and stock levels
3. **Notification Service** (Port 5003) - Sends notifications based on events

### Dapr Components Used

- **State Store**: Redis for persistent data storage
- **Pub/Sub**: Redis for event-driven communication between services
- **Service Invocation**: Direct service-to-service communication via Dapr sidecars

## Prerequisites

### Required Software

1. **Dapr CLI** - [Installation Guide](https://docs.dapr.io/getting-started/install-dapr-cli/)
2. **Docker Desktop** - [Download](https://www.docker.com/products/docker-desktop/)
3. **Python 3.9+** - [Download](https://www.python.org/downloads/)
4. **PowerShell** (Windows) or equivalent shell

### Verify Installations

```powershell
# Check Dapr installation
dapr --version

# Check Docker
docker --version

# Check Python
python --version
```

## Quick Start

### Option 1: Using PowerShell Scripts (Recommended)

1. **Start Redis and all services:**
   ```powershell
   .\scripts\start-services.ps1
   ```

2. **Run the demo test:**
   ```powershell
   .\scripts\demo-test.ps1
   ```

3. **Stop all services:**
   ```powershell
   .\scripts\stop-services.ps1
   ```

### Option 2: Manual Setup

1. **Start Redis:**
   ```powershell
   docker run -d --name redis-dapr -p 6379:6379 redis:7-alpine
   ```

2. **Install Python dependencies for each service:**
   ```powershell
   # Order Service
   cd order-service
   pip install -r requirements.txt
   
   # Inventory Service
   cd ../inventory-service
   pip install -r requirements.txt
   
   # Notification Service
   cd ../notification-service
   pip install -r requirements.txt
   ```

3. **Start each service with Dapr (in separate terminals):**
   ```powershell
   # Order Service
   cd order-service
   dapr run --app-id order-service --app-port 5001 --dapr-http-port 3500 --components-path ../dapr-components -- python app.py
   
   # Inventory Service
   cd inventory-service
   dapr run --app-id inventory-service --app-port 5002 --dapr-http-port 3501 --components-path ../dapr-components -- python app.py
   
   # Notification Service
   cd notification-service
   dapr run --app-id notification-service --app-port 5003 --dapr-http-port 3502 --components-path ../dapr-components -- python app.py
   ```

### Option 3: Using Docker Compose

```powershell
# Start all services with Docker
docker-compose up -d

# Note: This starts the apps but not the Dapr sidecars
# You'll need to start Dapr sidecars separately if using this option
```

## API Endpoints

### Order Service (Port 5001)

- `GET /health` - Health check
- `POST /orders` - Create new order
- `GET /orders/{order_id}` - Get order details
- `PUT /orders/{order_id}/status` - Update order status
- `GET /orders` - List orders (simplified)

### Inventory Service (Port 5002)

- `GET /health` - Health check
- `POST /inventory` - Add inventory
- `GET /inventory/{product_id}` - Get inventory for product
- `POST /inventory/{product_id}/reserve` - Reserve inventory

### Notification Service (Port 5003)

- `GET /health` - Health check
- `GET /notifications` - Get all notifications
- `POST /notifications` - Send custom notification
- `GET /notifications/customer/{customer_id}` - Get customer notifications

## Demo Scenarios

### Scenario 1: Basic Order Flow

```powershell
# 1. Add inventory
curl -X POST http://localhost:5002/inventory `
  -H "Content-Type: application/json" `
  -d '{"product_id": "laptop-001", "quantity": 10, "name": "Gaming Laptop", "price": 1299.99}'

# 2. Create order
curl -X POST http://localhost:5001/orders `
  -H "Content-Type: application/json" `
  -d '{
    "customer_id": "customer-123",
    "items": [
      {"product_id": "laptop-001", "quantity": 1, "price": 1299.99}
    ]
  }'

# 3. Check notifications
curl http://localhost:5003/notifications
```

### Scenario 2: Inventory Management

```powershell
# Check inventory
curl http://localhost:5002/inventory/laptop-001

# Reserve inventory
curl -X POST http://localhost:5002/inventory/laptop-001/reserve `
  -H "Content-Type: application/json" `
  -d '{"quantity": 2, "order_id": "test-order-123"}'
```

## Event Flow

1. **Order Created**: Order Service publishes `order_created` event
2. **Inventory Check**: Inventory Service receives event and checks stock
3. **Inventory Response**: Inventory Service publishes `inventory_checked` event
4. **Notifications**: Notification Service receives both events and sends notifications

## Project Structure

```
FOSS demo/
├── dapr-components/
│   ├── redis-pubsub.yaml      # Pub/sub component configuration
│   └── redis-statestore.yaml  # State store component configuration
├── order-service/
│   ├── app.py                 # Order service implementation
│   ├── requirements.txt       # Python dependencies
│   └── Dockerfile            # Container configuration
├── inventory-service/
│   ├── app.py                 # Inventory service implementation
│   ├── requirements.txt       # Python dependencies
│   └── Dockerfile            # Container configuration
├── notification-service/
│   ├── app.py                 # Notification service implementation
│   ├── requirements.txt       # Python dependencies
│   └── Dockerfile            # Container configuration
├── scripts/
│   ├── start-services.ps1     # Start all services
│   ├── stop-services.ps1      # Stop all services
│   └── demo-test.ps1         # Run demo test scenarios
├── docker-compose.yml         # Docker Compose configuration
└── README.md                 # This file
```

## Troubleshooting

### Common Issues

1. **Port Already in Use**
   ```powershell
   # Check what's using the port
   netstat -ano | findstr :5001
   
   # Kill the process
   taskkill /PID <process_id> /F
   ```

2. **Redis Connection Failed**
   ```powershell
   # Restart Redis
   docker restart redis-dapr
   
   # Or start fresh
   docker rm -f redis-dapr
   docker run -d --name redis-dapr -p 6379:6379 redis:7-alpine
   ```

3. **Dapr Sidecar Issues**
   ```powershell
   # Check Dapr status
   dapr list
   
   # Stop all Dapr apps
   dapr stop --app-id order-service
   dapr stop --app-id inventory-service
   dapr stop --app-id notification-service
   ```

### Logs and Debugging

- **Application Logs**: Check the PowerShell windows for each service
- **Dapr Logs**: Located in `%USERPROFILE%\.dapr\logs\`
- **Dapr Dashboard**: Run `dapr dashboard` to open the web UI

## Learning Resources

- [Dapr Documentation](https://docs.dapr.io/)
- [Dapr Python SDK](https://github.com/dapr/python-sdk)
- [Dapr Samples](https://github.com/dapr/samples)
- [Redis Documentation](https://redis.io/documentation)

## Next Steps

To extend this demo, consider:

1. **Add database persistence** instead of in-memory storage
2. **Implement proper error handling** and retry logic
3. **Add authentication and authorization**
4. **Include monitoring and observability** with Jaeger/Zipkin
5. **Deploy to Kubernetes** using Dapr Kubernetes operator
6. **Add more complex business logic** and workflows

## Contributing

Feel free to extend this demo with additional features or improvements!

## License

This demo is provided as-is for educational purposes.
