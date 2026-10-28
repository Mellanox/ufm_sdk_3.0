# HTTP Receiver for Fluent-bit

A simple Flask-based HTTP server that receives and displays logs from Fluent-bit's HTTP output plugin.

## Overview

This receiver accepts HTTP POST requests containing JSON-formatted log records from Fluent-bit and prints them to the console in a readable format.

## Installation

```bash
pip3 install -r http_receiver_requirements.txt
```

## Usage

### Start the receiver:
```bash
python3 http_receiver.py
```

Default configuration:
- **Host**: 0.0.0.0 (all interfaces)
- **Port**: 24226
- **Endpoint**: /api/logs

### Custom configuration:
```bash
python3 http_receiver.py --host 127.0.0.1 --port 8080 --endpoint /logs
```

## API Endpoint

### POST /api/logs

Receives log records from Fluent-bit.

**Request Format:**

Fluent-bit sends logs as a JSON array:

```json
[
  {
    "date": 1703505045.123,
    "pri": "30",
    "logger": "ufm",
    "severity": "INFO",
    "log_message": "UFM service started successfully",
  },
  {
    "date": 1703505046.456,
    "pri": "27",
    "logger": "ufm.events",
    "severity": "WARNING",
    "log_message": "Switch port state changed to DOWN",
  }
]
```

**Response Format:**

```json
{
  "status": "success",
  "received": 2
}
```

## Console Output

When logs are received, they are printed in the following format:

```
>>> Received 2 log record(s)
[2024-12-25 10:30:45.123] [INFO] [ufm] UFM service started successfully
[2024-12-25 10:30:46.456] [WARNING] [ufm.events] Switch port state changed to DOWN
```

Format: `[timestamp] [severity] [logger] message`

## Fluent-bit Configuration

To send logs to this receiver, configure Fluent-bit's HTTP output:

```ini
[OUTPUT]
    Name            http
    Match           *
    Host            <receiver_host>
    Port            24226
    URI             /api/logs
    Format          json
```

## Testing

Send a test request with curl:

```bash
curl -X POST http://localhost:24226/api/logs \
  -H "Content-Type: application/json" \
  -d '[{
    "date": 1703505045.123,
    "logger": "ufm",
    "severity": "INFO",
    "time": "2024-12-25 10:30:45.123",
    "message": "Test message"
  }]'
```

Expected response:
```json
{"status":"success","received":1}
```


## Command-line Options

| Option | Default | Description |
|--------|---------|-------------|
| `--host` | 0.0.0.0 | Host address to bind to |
| `--port` | 24226 | Port to listen on |
| `--endpoint` | /api/logs | Endpoint path for receiving logs |

## License

Copyright © 2013-2024 NVIDIA CORPORATION & AFFILIATES. ALL RIGHTS RESERVED.

