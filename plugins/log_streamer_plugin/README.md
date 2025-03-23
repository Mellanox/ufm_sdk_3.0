# Log Streamer Plugin

A Fluentd-based plugin for UFM that streams log files to a remote syslog server.

## Overview

The Log Streamer Plugin monitors specified log files and forwards their contents to a remote syslog server in real-time. It uses Fluentd for efficient log collection and forwarding, with support for multiple log files and configurable syslog settings.

## Features

- Real-time log file monitoring and streaming
- Support for multiple log files
- Configurable remote syslog destination
- Persistent log position tracking
- UDP/TCP protocol support
- Automatic log rotation handling

## Prerequisites

- Docker
- UFM environment
- Access to remote syslog server

## Configuration

### Main Configuration File

The plugin uses `log_streamer_conf.ini` for its main configuration:

```ini
[Common]
remote_syslog_addr = <syslog_server_ip>
remote_syslog_port = 514
remote_syslog_protocol = udp
files_to_stream = /path/to/file1.log,/path/to/file2.log
```

### Configuration Parameters

- `remote_syslog_addr`: IP address or hostname of the remote syslog server
- `remote_syslog_port`: Port number of the remote syslog server (default: 514)
- `remote_syslog_protocol`: Protocol to use (udp/tcp)
- `files_to_stream`: Comma-separated list of log files to monitor

## Installation

1. Build the Docker image:
   ```bash
   cd plugins/log_streamer_plugin/build
   docker build -t log-streamer .
   ```

2. Run the container:
   ```bash
   docker run -d \
     -v /path/to/logs:/var/log \
     -v /path/to/config:/etc/fluent \
     log-streamer
   ```

## Directory Structure

```
log_streamer_plugin/
├── build/
│   ├── Dockerfile
│   └── config/
│       └── log_streamer_conf.ini
├── conf/
│   └── supervisord_log_streamer.conf
├── scripts/
│   ├── init.sh
│   ├── deinit.sh
│   └── upgrade.sh
├── src/
│   ├── create_fluent_conf.sh
│   ├── log_streamer_entrypoint.sh
│   └── update_log_streamer_conf.sh
└── log_streamer_shared_volumes.conf
```

## Components

- `create_fluent_conf.sh`: Generates Fluentd configuration files
- `update_log_streamer_conf.sh`: Updates configuration from UFM settings
- `log_streamer_entrypoint.sh`: Container entrypoint script
- `init.sh`, `deinit.sh`, `upgrade.sh`: Plugin lifecycle management scripts

## Usage

### Starting the Plugin

The plugin automatically starts with UFM and begins monitoring configured log files. It creates necessary configuration files and maintains log positions in `/var/log/fluentd/`.

### Monitoring New Files

To monitor additional files:
1. Update the `files_to_stream` parameter in `log_streamer_conf.ini`
2. Restart the plugin

### Debugging

1. Check plugin status:
   ```bash
   docker ps | grep log-streamer
   ```

2. View plugin logs:
   ```bash
   docker logs <container_id>
   ```

3. Access container shell:
   ```bash
   docker exec -it <container_id> /bin/bash
   ```

## Troubleshooting

Common issues and solutions:

1. **Permission Denied**
   - Ensure proper permissions on log files
   - Run container with appropriate volume mounts

2. **Configuration Not Found**
   - Verify `log_streamer_conf.ini` location
   - Check file permissions

3. **Logs Not Forwarding**
   - Verify syslog server connectivity
   - Check Fluentd configuration files
   - Ensure correct file paths in configuration

## Development

### Building from Source

```bash
cd plugins/log_streamer_plugin
docker build -t log-streamer:dev -f build/Dockerfile .
```

### Testing

1. Run with test configuration:
   ```bash
   docker run -it --rm \
     -v $(pwd)/test/config:/etc/fluent \
     log-streamer:dev
   ```

2. Verify log forwarding:
   ```bash
   nc -ul 514  # Listen on UDP port 514
   ```

## License

Copyright (c) 2013-2024 NVIDIA CORPORATION & AFFILIATES. ALL RIGHTS RESERVED.

This software product is a proprietary product of Nvidia Corporation and its affiliates.
