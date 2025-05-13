from pygnmi.client import gNMIclient
import json
import time
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run():
    # Create a gNMI client
    with gNMIclient(
        target=('localhost', 9339),
        username='',  # Empty string instead of None
        password='',  # Empty string instead of None
        insecure=True,
        skip_verify=True
    ) as client:
        logger.info("Connected to gNMI simulator. Waiting for events...")
        
        # Subscribe to system events
        subscribe = {
            'subscription': [
                {
                    'path': 'system/events',  # Path as a string with '/' separator
                    'mode': 'SAMPLE',  # Use SAMPLE mode with interval
                    'sample_interval': 5000000000  # 5 seconds in nanoseconds
                }
            ],
            'mode': 'STREAM',
            'encoding': 'JSON'
        }
        
        # Subscribe to all paths using subscribe_stream
        try:
            for response in client.subscribe_stream(subscribe=subscribe):
                logger.info(f"\nReceived response: {response}")
                
                # Check for sync_response
                if response.get('sync_response'):
                    logger.info("Initial sync completed")
                    continue
                
                # Extract update information
                event_update = response.get('update', {})
                if event_update:
                    update = event_update.get('update', [])
                    for item in update:
                        path = item.get('path', '')
                        val = item.get('val', {})
                        
                        # Format the path
                        path_str = path if isinstance(path, str) else '/'.join(path)
                        logger.info(f"Path: {path_str}")
                        
                        # Format the value
                        if isinstance(val, dict):
                            logger.info(f"Value: {json.dumps(val, indent=2)}")
                        else:
                            logger.info(f"Value: {val}")
                        
        except KeyboardInterrupt:
            logger.info("\nStopping client...")
        except Exception as e:
            logger.error(f"Error: {str(e)}")
            raise

if __name__ == '__main__':
    run() 