#!/bin/bash -x

PLUGIN_DIR="plugins/pdr_deterministic_plugin"
pip install -r $PLUGIN_DIR/requirements.txt >/dev/null 2>&1

cp -r utils $PLUGIN_DIR/ufm_sim_web_service
cp -r utils $PLUGIN_DIR/tests

echo "Init PDR configuration file"
CONFIG_FILE="/config/pdr_deterministic.conf"
mkdir -p /config
cp -f $PLUGIN_DIR/build/config/pdr_deterministic.conf "$CONFIG_FILE"
sed -i -e 's/\nTEST_MODE=\n//g' "$CONFIG_FILE" # Remove any existing TEST_MODE lines from the file
echo -e '\n[Common]\nTEST_MODE=True\n' >> "$CONFIG_FILE"
sed -i -e 's/DRY_RUN=False/DRY_RUN=True/g' "$CONFIG_FILE"
sed -i -e 's/INTERVAL=300/INTERVAL=10/g' "$CONFIG_FILE"
sed -i -e 's/CONFIGURED_TEMP_CHECK=False/CONFIGURED_TEMP_CHECK=True/g' "$CONFIG_FILE"
sed -i -e 's/LINK_DOWN_ISOLATION=False/LINK_DOWN_ISOLATION=True/g' "$CONFIG_FILE"
sed -i -e 's/DEISOLATE_CONSIDER_TIME=5/DEISOLATE_CONSIDER_TIME=1/g' "$CONFIG_FILE"

"Terminating standalone PDR process"
pkill -9 -f isolation_algo.py 2>/dev/null || true
sleep 10

echo "Starting standalone PDR process"
python $PLUGIN_DIR/ufm_sim_web_service/isolation_algo.py >/dev/null 2>&1 &
