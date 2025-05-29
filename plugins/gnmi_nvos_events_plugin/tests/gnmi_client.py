import grpc
import time
import json
from gnmi.gnmi_pb2 import (
    SubscribeRequest,
    SubscriptionList,
    Subscription,
    SubscriptionMode
)
from gnmi.gnmi_pb2_grpc import gNMIStub

def run():
    # Create a gRPC channel
    channel = grpc.insecure_channel('localhost:9339')
    stub = gNMIStub(channel)

    # Create a subscription request
    subscribe_request = SubscribeRequest(
        subscribe=SubscriptionList(
            subscription=[
                Subscription(
                    path=None,  # Subscribe to all paths
                    mode=SubscriptionMode.ON_CHANGE
                )
            ],
            mode='STREAM'
        )
    )

    try:
        # Create subscription stream
        stream = stub.Subscribe(iter([subscribe_request]))
        
        print("Connected to gNMI simulator. Waiting for events...")
        
        # Receive events
        for response in stream:
            print("\nReceived event:")
            print(f"Timestamp: {response.update.timestamp}")
            for update in response.update.update:
                path_str = "/".join(elem.name for elem in update.path.elem)
                print(f"Path: {path_str}")
                event_data = json.loads(update.val.json_val.decode())
                print(f"Value: {json.dumps(event_data, indent=2)}")
                
    except grpc.RpcError as e:
        print(f"gRPC error: {e}")
    except KeyboardInterrupt:
        print("\nStopping client...")
    finally:
        channel.close()

if __name__ == '__main__':
    run() 