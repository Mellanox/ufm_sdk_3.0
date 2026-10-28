#!/usr/bin/env python3
#
# Copyright © 2013-2024 NVIDIA CORPORATION & AFFILIATES. ALL RIGHTS RESERVED.
#
# This software product is a proprietary product of Nvidia Corporation and its affiliates
# (the "Company") and all right, title, and interest in and to the software
# product, including all associated intellectual property rights, are and
# shall remain exclusively with the Company.
#
# This software product is governed by the End User License Agreement
# provided with the software product.
#

"""
Simple HTTP receiver for Fluent-bit HTTP output
This server receives JSON logs from Fluent-bit and prints them to console.

Usage:
    python3 http_receiver.py [--host HOST] [--port PORT] [--endpoint ENDPOINT]

Example:
    python3 http_receiver.py --host 0.0.0.0 --port 24226 --endpoint /api/logs
"""

import argparse
import json
from datetime import datetime
from flask import Flask, request, jsonify

app = Flask(__name__)

# Global configuration
CONFIG = {
    'host': '0.0.0.0',
    'port': 24226,
    'endpoint': '/api/logs'
}


def process_log_record(record):
    """Process a single log record - customize this based on your needs"""
    # Extract key fields
    timestamp = record.get('time', record.get('date', 'N/A'))
    severity = record.get('severity', record.get('event_severity', 'INFO'))
    message = record.get('message', record.get('log_message', 'N/A'))
    logger_name = record.get('logger', 'unknown')
    
    # Print to console
    print(f"[{timestamp}] [{severity}] [{logger_name}] {message}")
    
    # Here you can add custom processing:
    # - Send to another system
    # - Store in database
    # - Trigger alerts
    # - Filter specific events
    
    return record


@app.route(CONFIG['endpoint'], methods=['POST'])
def receive_logs():
    """
    Main endpoint to receive logs from Fluent-bit
    
    Fluent-bit sends logs as JSON array:
    [
        {"date": 1234567890, "field1": "value1", ...},
        {"date": 1234567891, "field2": "value2", ...}
    ]
    """
    try:
        # Get the JSON payload
        data = request.get_json()
        
        if data is None:
            print("ERROR: Received empty or invalid JSON payload")
            return jsonify({'error': 'Invalid JSON payload'}), 400
        
        # Fluent-bit sends array of records
        if isinstance(data, list):
            log_records = data
        elif isinstance(data, dict):
            # Single record
            log_records = [data]
        else:
            print(f"ERROR: Unexpected data type: {type(data)}")
            return jsonify({'error': 'Invalid data format'}), 400
        
        print(f"\n>>> Received {len(log_records)} log record(s)")
        
        # Process each log record
        for record in log_records:
            process_log_record(record)
        
        # Return success response
        return jsonify({
            'status': 'success',
            'received': len(log_records)
        }), 200
        
    except Exception as e:
        print(f"ERROR: Error processing logs: {str(e)}")
        return jsonify({
            'error': 'Internal server error',
            'message': str(e)
        }), 500


def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description='Simple HTTP receiver for Fluent-bit logs',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    parser.add_argument(
        '--host',
        type=str,
        default='0.0.0.0',
        help='Host address to bind to'
    )
    
    parser.add_argument(
        '--port',
        type=int,
        default=24226,
        help='Port to listen on'
    )
    
    parser.add_argument(
        '--endpoint',
        type=str,
        default='/api/logs',
        help='Endpoint path to receive logs'
    )
    
    return parser.parse_args()


def main():
    """Main function"""
    args = parse_arguments()
    
    # Update configuration
    CONFIG['host'] = args.host
    CONFIG['port'] = args.port
    CONFIG['endpoint'] = args.endpoint
    
    # Print startup information
    print("=" * 60)
    print("UFM Log Receiver - Simple HTTP Server")
    print("=" * 60)
    print(f"Listening on: http://{CONFIG['host']}:{CONFIG['port']}")
    print(f"Endpoint: POST {CONFIG['endpoint']}")
    print("=" * 60)
    print("\nWaiting for logs from Fluent-bit...")
    print("Press Ctrl+C to stop the server\n")
    print("=" * 60)
    
    # Run the Flask server
    try:
        app.run(
            host=CONFIG['host'],
            port=CONFIG['port'],
            debug=False,
            threaded=True
        )
    except KeyboardInterrupt:
        print("\n\nShutting down server...")
        print("Goodbye!")
    except Exception as e:
        print(f"\nError starting server: {str(e)}")
        exit(1)


if __name__ == '__main__':
    main()

