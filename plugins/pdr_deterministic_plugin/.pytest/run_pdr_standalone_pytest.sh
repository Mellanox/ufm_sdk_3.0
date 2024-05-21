#!/bin/bash -x

PLUGIN_DIR="plugins/pdr_deterministic_plugin"
pip install -r $PLUGIN_DIR/requirements.txt >/dev/null 2>&1

cp -r utils $PLUGIN_DIR/ufm_sim_web_service
cp -r utils $PLUGIN_DIR/tests

echo "Init PDR configuration file"
CONFIG_FILE="/config/pdr_deterministic.conf"
mkdir -p /config
cp -f $PLUGIN_DIR/build/config/pdr_deterministic.conf "$CONFIG_FILE"
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

bash $PLUGIN_DIR/.pytest/terminate_pdr_standalone_pytest.sh
echo "Starting standalone PDR process"
python $PLUGIN_DIR/ufm_sim_web_service/isolation_algo.py >/dev/null 2>&1 &
sleep 10
if ! ps aux | grep -q [i]solation_algo.py; then
    echo "Failed to start standalone PDR process"
    exit 1
fi
# PDR is up and ready for communication