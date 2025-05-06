# gNMI Event Simulator

This directory contains a gNMI event simulator that can be used for testing gNMI clients and applications. The simulator generates random events and streams them using the gNMI protocol.

## Components

- `gnmi_simulator.py`: The gNMI server that generates and streams events
- `gnmi_client.py`: A sample client using raw gRPC/gNMI
- `gnmi_client_pygnmi.py`: A sample client using the pygnmi library
- `generate_protos.py`: Script to generate gNMI protobuf files
- `requirements.txt`: Python dependencies

## Why Protocol Buffers?

The simulator uses Protocol Buffers (protobuf) for several important reasons:

1. **Protocol Definition**: 
   - gNMI is defined using Protocol Buffers
   - The `.proto` files define the exact structure of messages and RPCs
   - They serve as a contract between client and server

2. **Code Generation**:
   - The `.proto` files are used to generate Python code (`gnmi_pb2.py` and `gnmi_pb2_grpc.py`)
   - This generated code provides:
     - Message classes (e.g., `SubscribeRequest`, `Notification`)
     - RPC service definitions
     - Serialization/deserialization logic

3. **Protocol Compliance**:
   - Ensures our simulator follows the gNMI protocol specification
   - Makes it compatible with other gNMI clients and servers

## Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Generate protobuf files:
   ```bash
   python generate_protos.py
   ```

## Usage

1. Start the simulator:
   ```bash
   python gnmi_simulator.py
   ```
   The simulator will start on port 9339 and begin generating random events.

2. Run one of the sample clients:
   ```bash
   # Using raw gRPC/gNMI
   python gnmi_client.py
   
   # Using pygnmi library
   python gnmi_client_pygnmi.py
   ```
   Both clients will connect to the simulator and display received events.

## Client Options

The simulator comes with two different client implementations:

1. **Raw gRPC/gNMI Client** (`gnmi_client.py`):
   - Uses the generated protobuf code directly
   - More low-level control over the gNMI protocol
   - Good for understanding the protocol internals

2. **pygnmi Client** (`gnmi_client_pygnmi.py`):
   - Uses the higher-level pygnmi library
   - More concise and easier to use
   - Handles many protocol details automatically
   - Better for production use

## Event Format

The simulator generates events with the following structure:
- Path: One of `system/status`, `interface/state`, `port/status`, `temperature/sensor`, `power/status`
- Value: JSON object containing:
  - `severity`: One of "INFO", "WARNING", "ERROR", "CRITICAL"
  - `value`: Random number between 0 and 100
  - `description`: Event description

Example event:
```json
{
  "severity": "WARNING",
  "value": 75,
  "description": "Simulated system/status event"
}
```

## Implementation Details

The simulator implements the gNMI protocol's Subscribe RPC and uses gRPC for communication. It:
1. Creates a gRPC server listening on port 9339
2. Accepts subscription requests from clients
3. Generates random events every 1-5 seconds
4. Streams events to connected clients

The sample clients demonstrate how to:
1. Connect to the gNMI server
2. Create a subscription request
3. Receive and parse events from the stream

## Stopping the Simulator

To stop the simulator, use:
```bash
pkill -f gnmi_simulator.py
``` 