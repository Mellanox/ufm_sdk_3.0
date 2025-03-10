#!/bin/bash
# Entry point script for log streamer plugin - updates config and starts fluentd
rm -f /fluentd/etc/fluent.conf

# Update log_streamer_conf.ini with gv.cfg settings
/update_log_streamer_conf.sh

# Create fluent.conf
/create_fluent_conf.sh

# Start fluentd
if [ -f /fluentd/etc/fluent.conf ]; then
    exec fluentd -c /fluentd/etc/fluent.conf
else
    echo "fluent.conf not found"
fi
