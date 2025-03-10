#!/bin/bash

# Set absolute paths
CONFIG_FILE="/log_streamer_conf.ini"
CONF_DIR="./conf"
FLUENTD_CONF_DIR="/fluentd/etc"
POS_DIR="/var/log/fluentd"  # Default pos file directory

# Create conf directory if it doesn't exist
mkdir -p "$CONF_DIR"

# Function to read configuration from ini file
read_config() {
    local key=$1
    local default_value=${2:-""}  # If no default value provided, use empty string
    local value
    
    value=$(grep "^[[:space:]]*$key[[:space:]]*=" "$CONFIG_FILE" 2>/dev/null | cut -d'=' -f2 | tr -d ' ')
    if [ -z "$value" ]; then
        echo "$default_value"
    else
        echo "$value"
    fi
}

# Function to get just the filename without path and extension
get_filename() {
    local file=$1
    basename "${file%.*}" | sed 's|.*/||'
}

# Function to copy configurations to Fluentd directory
copy_to_fluentd() {
    echo "Copying configurations to ${FLUENTD_CONF_DIR}..."
    
    # Remove existing configurations in Fluentd directory
    rm -f "${FLUENTD_CONF_DIR}"/*.conf
    
    # Copy all new configurations
    cp -v "${CONF_DIR}"/*.conf "${FLUENTD_CONF_DIR}/" || {
        echo "Error: Failed to copy configurations to ${FLUENTD_CONF_DIR}"
        return 1
    }
    
    echo "Successfully copied configurations to ${FLUENTD_CONF_DIR}"
    return 0
}

# Function to create main fluent.conf
create_main_fluent_conf() {
    local remote_addr=$1
    local remote_port=$2
    local remote_protocol=$3

    cat > "$CONF_DIR/fluent.conf" << EOF
@include /fluentd/etc/*_fluent.conf

<match *.log>
  @type remote_syslog
  host ${remote_addr}
  port ${remote_port}
  protocol ${remote_protocol}
  program \${tag}
  <buffer tag>
    @type memory
    flush_mode immediate
  </buffer>
</match>
EOF
}

# Function to create individual file configuration
create_file_fluent_conf() {
    local file=$1
    local filename=$(get_filename "$file")
    local conf_file="$CONF_DIR/${filename%.*}_fluent.conf"
    local pos_filename=$(get_filename "$file")
    
    # Create pos directory if it doesn't exist
    mkdir -p "$POS_DIR"
    
    # Create individual fluent configuration file
    cat > "$conf_file" << EOF
<source>
  @type tail
  path ${file}
  pos_file ${POS_DIR}/${pos_filename}.pos
  tag ${pos_filename}
  format none
</source>
EOF
}

# Main function to execute the configuration creation
main() {
    local ret=0

    # Read syslog configuration
    REMOTE_SYSLOG_ADDR=$(read_config "remote_syslog_addr")
    REMOTE_SYSLOG_PORT=$(read_config "remote_syslog_port" "514")
    REMOTE_SYSLOG_PROTOCOL=$(read_config "remote_syslog_protocol" "udp")

    # Check if configuration values are empty
    if [ -z "$REMOTE_SYSLOG_ADDR" ]; then
        echo "Error: Missing required syslog configuration values"
        return 1
    fi

    # Create main fluent.conf
    if ! create_main_fluent_conf "$REMOTE_SYSLOG_ADDR" "$REMOTE_SYSLOG_PORT" "$REMOTE_SYSLOG_PROTOCOL"; then
        echo "Error: Failed to create main fluent.conf"
        return 1
    fi

    # Read and process files to stream
    FILES_TO_STREAM=$(read_config "files_to_stream")
    if [ -z "$FILES_TO_STREAM" ]; then
        rm -f "$CONF_DIR/fluent.conf"
        echo "Error: No files specified for streaming"
        return 1
    fi

    IFS=',' read -ra FILES <<< "$FILES_TO_STREAM"
    for file in "${FILES[@]}"; do
        # Trim whitespace
        file=$(echo "$file" | tr -d ' ')
        if ! create_file_fluent_conf "$file"; then
            echo "Error: Failed to create configuration for file: $file"
            ret=1
        fi
    done

    if [ $ret -eq 0 ]; then
        echo "Success: Fluentd configuration files have been created successfully."
        # Copy configurations to Fluentd directory if everything succeeded
        if ! copy_to_fluentd; then
            echo "Error: Failed to copy configurations to Fluentd directory"
            return 1
        fi
    else
        echo "Warning: Some configuration files failed to create."
    fi

    return $ret
}

# Execute main function and exit with its return value
main
exit $?