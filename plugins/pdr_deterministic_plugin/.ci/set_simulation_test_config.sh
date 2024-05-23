#!/bin/bash -x

#CONFIG_FILE="/opt/ufm/files/conf/plugins/pdr_deterministic/pdr_deterministic.conf"
CONFIG_FILE="plugins/pdr_deterministic_plugin/build/config/pdr_deterministic.conf"

sed -i -e 's/DRY_RUN=False/DRY_RUN=True/g' "$CONFIG_FILE"
sed -i -e 's/INTERVAL=300/INTERVAL=10/g' "$CONFIG_FILE"
sed -i -e 's/CONFIGURED_TEMP_CHECK=False/CONFIGURED_TEMP_CHECK=True/g' "$CONFIG_FILE"
sed -i -e 's/LINK_DOWN_ISOLATION=False/LINK_DOWN_ISOLATION=True/g' "$CONFIG_FILE"
sed -i -e 's/DEISOLATE_CONSIDER_TIME=5/DEISOLATE_CONSIDER_TIME=1/g' "$CONFIG_FILE"

# Remove any existing TEST_MODE lines from the file
sed -i -e '/TEST_MODE=\(True\|False\)/d' "$CONFIG_FILE"

# Check if the section [Common] exists
if grep -q '^\[Common\]' "$CONFIG_FILE"; then
    # If section exists, insert TEST_MODE=True under it
    awk '/^\[Common\]/ {print; print "TEST_MODE=True"; next}1' "$CONFIG_FILE" > temp && mv temp "$CONFIG_FILE"
else
    # If section does not exist, add it to the file
    echo -e '\n[Common]\nTEST_MODE=True\n' >> "$CONFIG_FILE"
fi
