# Dapr Microservices Architecture

This document describes the architecture of the Dapr-based microservices demo, showing how Dapr facilitates service communication, state management, and event-driven messaging.

## Overall Architecture

```mermaid
graph TB
    %% Client Layer
    Client[Demo Test Script<br/>PowerShell Client]
    
    %% Application Services
    subgraph "Application Services"
        OrderApp[Order Service<br/>Flask App<br/>Port 5001]
        InventoryApp[Inventory Service<br/>Flask App<br/>Port 5002]
        NotificationApp[Notification Service<br/>Flask App<br/>Port 5003]
    end
    
    %% Dapr Sidecars
    subgraph "Dapr Sidecars"
        OrderDapr[Order Dapr Sidecar<br/>HTTP: 3500]
        InventoryDapr[Inventory Dapr Sidecar<br/>HTTP: 3501]
        NotificationDapr[Notification Dapr Sidecar<br/>HTTP: 3502]
    end
    
    %% Infrastructure
    subgraph "Infrastructure Components"
        Redis[(Redis<br/>State Store &<br/>Pub/Sub Broker<br/>Port 6379)]
    end
    
    %% Dapr Components
    subgraph "Dapr Components"
        StateStore[Redis State Store<br/>redis-statestore.yaml]
        PubSub[Redis Pub/Sub<br/>redis-pubsub.yaml]
    end
    
    %% Client to Services
    Client -->|HTTP REST API| OrderApp
    Client -->|HTTP REST API| InventoryApp
    Client -->|HTTP REST API| NotificationApp
    
    %% Apps to Dapr Sidecars
    OrderApp <-->|HTTP| OrderDapr
    InventoryApp <-->|HTTP| InventoryDapr
    NotificationApp <-->|HTTP| NotificationDapr
    
    %% Dapr to Infrastructure
    OrderDapr <-->|State API| StateStore
    InventoryDapr <-->|State API| StateStore
    NotificationDapr <-->|State API| StateStore
    
    OrderDapr <-->|Pub/Sub API| PubSub
    InventoryDapr <-->|Pub/Sub API| PubSub
    NotificationDapr <-->|Pub/Sub API| PubSub
    
    %% Components to Redis
    StateStore <-->|TCP| Redis
    PubSub <-->|TCP| Redis
    
    %% Styling
    classDef appService fill:#e1f5fe,stroke:#01579b,stroke-width:2px
    classDef daprSidecar fill:#fff3e0,stroke:#e65100,stroke-width:2px
    classDef infrastructure fill:#f3e5f5,stroke:#4a148c,stroke-width:2px
    classDef daprComponent fill:#e8f5e8,stroke:#1b5e20,stroke-width:2px
    classDef client fill:#fff8e1,stroke:#f57f17,stroke-width:2px
    
    class OrderApp,InventoryApp,NotificationApp appService
    class OrderDapr,InventoryDapr,NotificationDapr daprSidecar
    class Redis infrastructure
    class StateStore,PubSub daprComponent
    class Client client
```

## Data Flow and Event Sequence

```mermaid
sequenceDiagram
    participant Client as Demo Script
    participant OrderApp as Order Service
    participant OrderDapr as Order Dapr
    participant PubSub as Redis Pub/Sub
    participant InventoryDapr as Inventory Dapr
    participant InventoryApp as Inventory Service
    participant StateStore as Redis State Store
    participant NotificationDapr as Notification Dapr
    participant NotificationApp as Notification Service
    
    %% Order Creation Flow
    Client->>+OrderApp: POST /orders (Create Order)
    OrderApp->>+OrderDapr: Save order to state store
    OrderDapr->>+StateStore: Store order data
    StateStore-->>-OrderDapr: Confirm storage
    OrderDapr-->>-OrderApp: Storage confirmed
    
    OrderApp->>+OrderDapr: Publish order_created event
    OrderDapr->>+PubSub: Publish to order-events topic
    PubSub-->>-OrderDapr: Event published
    OrderDapr-->>-OrderApp: Publish confirmed
    OrderApp-->>-Client: Order created response
    
    %% Event Distribution
    PubSub->>+InventoryDapr: order_created event
    PubSub->>+NotificationDapr: order_created event
    
    %% Inventory Processing
    InventoryDapr->>+InventoryApp: /handle-order-event
    InventoryApp->>+InventoryDapr: Get inventory from state store
    InventoryDapr->>+StateStore: Retrieve inventory data
    StateStore-->>-InventoryDapr: Return inventory
    InventoryDapr-->>-InventoryApp: Inventory data
    
    InventoryApp->>+InventoryDapr: Update inventory (reserve items)
    InventoryDapr->>+StateStore: Update inventory quantities
    StateStore-->>-InventoryDapr: Update confirmed
    InventoryDapr-->>-InventoryApp: Update confirmed
    
    InventoryApp->>+InventoryDapr: Publish inventory_processed event
    InventoryDapr->>+PubSub: Publish to inventory-events topic
    PubSub-->>-InventoryDapr: Event published
    InventoryDapr-->>-InventoryApp: Response
    InventoryApp-->>-InventoryDapr: Complete
    
    %% Notification Processing
    NotificationDapr->>+NotificationApp: /handle-order-event
    NotificationApp->>NotificationApp: Create order confirmation notification
    NotificationApp->>+NotificationDapr: Store notification in state
    NotificationDapr->>+StateStore: Store notification
    StateStore-->>-NotificationDapr: Stored
    NotificationDapr-->>-NotificationApp: Complete
    NotificationApp-->>-NotificationDapr: Response
    
    %% Inventory Event to Notifications
    PubSub->>+NotificationDapr: inventory_processed event
    NotificationDapr->>+NotificationApp: /handle-inventory-event
    NotificationApp->>NotificationApp: Create inventory notification
    NotificationApp->>+NotificationDapr: Store notification in state
    NotificationDapr->>+StateStore: Store notification
    StateStore-->>-NotificationDapr: Stored
    NotificationDapr-->>-NotificationApp: Complete
    NotificationApp-->>-NotificationDapr: Response
```

## Dapr Building Blocks Used

```mermaid
graph LR
    subgraph "Dapr Building Blocks"
        StateAPI[State Management API<br/>Key-Value Store]
        PubSubAPI[Pub/Sub API<br/>Event Messaging]
        ServiceAPI[Service Invocation API<br/>HTTP/gRPC calls]
    end
    
    subgraph "Application Benefits"
        Resilience[Built-in Resilience<br/>Retries, Circuit Breakers]
        Observability[Automatic Observability<br/>Metrics, Tracing, Logs]
        Security[Security Features<br/>mTLS, Access Control]
        Portability[Infrastructure Agnostic<br/>Multi-cloud Ready]
    end
    
    StateAPI --> Resilience
    PubSubAPI --> Observability
    ServiceAPI --> Security
    StateAPI --> Portability
    PubSubAPI --> Resilience
    ServiceAPI --> Observability
    
    classDef buildingBlock fill:#e3f2fd,stroke:#1565c0,stroke-width:2px
    classDef benefit fill:#f1f8e9,stroke:#33691e,stroke-width:2px
    
    class StateAPI,PubSubAPI,ServiceAPI buildingBlock
    class Resilience,Observability,Security,Portability benefit
```

## Component Configuration

```mermaid
graph TB
    subgraph "Dapr Components Configuration"
        subgraph "State Store Component"
            StateConfig[redis-statestore.yaml<br/>---<br/>apiVersion: dapr.io/v1alpha1<br/>kind: Component<br/>metadata:<br/>  name: redis-statestore<br/>spec:<br/>  type: state.redis<br/>  metadata:<br/>  - name: redisHost<br/>    value: localhost:6379]
        end
        
        subgraph "Pub/Sub Component" 
            PubSubConfig[redis-pubsub.yaml<br/>---<br/>apiVersion: dapr.io/v1alpha1<br/>kind: Component<br/>metadata:<br/>  name: redis-pubsub<br/>spec:<br/>  type: pubsub.redis<br/>  metadata:<br/>  - name: redisHost<br/>    value: localhost:6379]
        end
    end
    
    subgraph "Application Usage"
        StateUsage[State Store Usage:<br/>• Order storage<br/>• Inventory tracking<br/>• Notification history<br/>• Reservation records]
        
        PubSubUsage[Pub/Sub Usage:<br/>• order-events topic<br/>• inventory-events topic<br/>• Event-driven workflows<br/>• Decoupled communication]
    end
    
    StateConfig --> StateUsage
    PubSubConfig --> PubSubUsage
    
    classDef config fill:#fff3e0,stroke:#e65100,stroke-width:2px
    classDef usage fill:#e8f5e8,stroke:#2e7d32,stroke-width:2px
    
    class StateConfig,PubSubConfig config
    class StateUsage,PubSubUsage usage
```

## Key Dapr Features Demonstrated

### 1. **State Management**
- **What Dapr Does**: Provides a consistent key-value API across different state stores
- **In Our Solution**: 
  - Orders stored as `order:{order_id}`
  - Inventory tracked as `inventory:{product_id}`
  - Notifications stored as `notification:{notification_id}`
  - Reservations tracked as `reservation:{order_id}:{product_id}`

### 2. **Pub/Sub Messaging**
- **What Dapr Does**: Abstracts message broker complexities with standard publish/subscribe API
- **In Our Solution**:
  - `order-events` topic for order lifecycle events
  - `inventory-events` topic for inventory status updates
  - Automatic event delivery to subscribers
  - CloudEvents format standardization

### 3. **Service Discovery & Communication**
- **What Dapr Does**: Simplifies service-to-service communication with built-in service discovery
- **In Our Solution**: Each service communicates through its Dapr sidecar using standard HTTP

### 4. **Infrastructure Abstraction**
- **What Dapr Does**: Provides pluggable components for different infrastructure providers
- **In Our Solution**: Redis components can be swapped for other providers (Azure Service Bus, AWS SQS, etc.) without code changes

## Benefits of This Architecture

1. **Loose Coupling**: Services communicate through events, not direct calls
2. **Resilience**: Dapr handles retries, timeouts, and circuit breaking
3. **Observability**: Automatic metrics and tracing across all services
4. **Portability**: Same code works across different cloud providers
5. **Simplified Development**: Developers focus on business logic, not infrastructure concerns
6. **Event-Driven**: Reactive architecture that scales based on demand