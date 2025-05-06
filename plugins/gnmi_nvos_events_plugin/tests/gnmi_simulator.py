import grpc
from concurrent import futures
import time
import random
import logging
import json
from typing import Generator, Dict, Any

# Import generated gNMI protobuf files
from gnmi.gnmi_pb2 import (
    SubscribeRequest,
    SubscribeResponse,
    Notification,
    Update,
    Path,
    PathElem,
    TypedValue,
    Encoding,
    SubscriptionList,
    Subscription,
    SubscriptionMode,
    CapabilityResponse,
    ModelData
)
from gnmi.gnmi_pb2_grpc import (
    gNMIStub,
    gNMIServicer,
    add_gNMIServicer_to_server
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GNMIEventSimulator(gNMIServicer):
    """
    A gNMI server simulator that can stream simulated events
    """
    def __init__(self):
        self.subscriptions: Dict[str, Generator] = {}
        self.event_types = [
            ("system", "events"),
            ("interface", "state"),
            ("port", "status"),
            ("temperature", "sensor"),
            ("power", "status")
        ]
        self.severity_levels = ["INFO", "WARNING", "ERROR", "CRITICAL"]
        
    def Capabilities(self, request, context):
        """
        Implement the Capabilities RPC
        """
        logger.info("Received Capabilities request")
        return CapabilityResponse(
            supported_models=[
                ModelData(
                    name="openconfig",
                    organization="OpenConfig",
                    version="1.0.0"
                )
            ],
            supported_encodings=[Encoding.JSON],
            gNMI_version="0.7.0"
        )
        
    def Subscribe(self, request_iterator, context):
        """
        Handle gNMI Subscribe requests and stream simulated events
        """
        try:
            for request in request_iterator:
                logger.info(f"Received subscription request: {request}")
                if request.HasField('subscribe'):
                    subscription_list = request.subscribe
                    logger.info(f"Subscription list: {subscription_list}")
                    
                    # Create a generator for this subscription
                    event_generator = self._generate_events(subscription_list)
                    
                    # Stream events
                    for event in event_generator:
                        if context.is_active():
                            logger.info(f"Sending event: {event}")
                            yield event
                        else:
                            logger.info("Context is no longer active")
                            break
                            
        except Exception as e:
            logger.error(f"Error in Subscribe: {str(e)}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            
    def _generate_events(self, subscription_list: SubscriptionList) -> Generator[SubscribeResponse, None, None]:
        """
        Generate simulated events based on subscription configuration
        """
        # Get sample interval from subscription or use default
        sample_interval = 5.0  # default 5 seconds
        
        try:
            if subscription_list.subscription:
                for sub in subscription_list.subscription:
                    if hasattr(sub, 'sample_interval'):
                        # Convert from nanoseconds to seconds
                        sample_interval = float(sub.sample_interval) / 1e9
                        break
            
            logger.info(f"Using sample interval: {sample_interval} seconds")
            
            # Send initial sync response
            yield SubscribeResponse(sync_response=True)
            
            while True:
                # For now, only generate system events since that's what the client is subscribing to
                event_type = ("system", "events")
                severity = random.choice(self.severity_levels)
                value = random.randint(0, 100)
                
                # Create path with proper PathElem objects
                path = Path(elem=[
                    PathElem(name=event_type[0]),
                    PathElem(name=event_type[1])
                ])
                
                # Create event data
                event_data = {
                    "severity": severity,
                    "value": value,
                    "description": f"Simulated {event_type[0]}/{event_type[1]} event"
                }
                
                # Create notification
                notification = Notification(
                    timestamp=int(time.time() * 1000000000),  # nanoseconds
                    update=[
                        Update(
                            path=path,
                            val=TypedValue(
                                json_val=json.dumps(event_data).encode()
                            )
                        )
                    ]
                )
                
                # Create and yield response
                response = SubscribeResponse(update=notification)
                logger.info(f"Sending event: {event_data}")
                yield response
                
                # Use the sample interval from subscription
                time.sleep(sample_interval)
                
        except Exception as e:
            logger.error(f"Error in event generation: {str(e)}")
            raise

def serve(port: int = 9339):
    """
    Start the gNMI simulator server
    """
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    add_gNMIServicer_to_server(GNMIEventSimulator(), server)
    server.add_insecure_port(f'[::]:{port}')
    server.start()
    logger.info(f"gNMI Simulator server started on port {port}")
    try:
        server.wait_for_termination()
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
        server.stop(0)

if __name__ == '__main__':
    serve()