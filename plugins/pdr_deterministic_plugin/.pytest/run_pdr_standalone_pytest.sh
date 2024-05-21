#!/bin/bash -x

PLUGIN_DIR="plugins/pdr_deterministic_plugin"
pip install -r $PLUGIN_DIR/requirements.txt >/dev/null 2>&1

cp -r utils $PLUGIN_DIR/ufm_sim_web_service
cp -r utils $PLUGIN_DIR/tests

echo "Init PDR configuration file"
CONFIG_FILE="/config/pdr_deterministic.conf"
mkdir -p /config
cp -f $PLUGIN_DIR/build/config/pdr_deterministic.conf "$CONFIG_FILE"
sed -i -e 's/\nTEST_MODE=True\n//g' "$CONFIG_FILE"
echo -e '\n[Common]\nTEST_MODE=True\n' >> "$CONFIG_FILE"
sed -i -e 's/DRY_RUN=False/DRY_RUN=True/g' "$CONFIG_FILE"
sed -i -e 's/INTERVAL=300/INTERVAL=10/g' "$CONFIG_FILE"
sed -i -e 's/CONFIGURED_TEMP_CHECK=False/CONFIGURED_TEMP_CHECK=True/g' "$CONFIG_FILE"
sed -i -e 's/DEISOLATE_CONSIDER_TIME=5/DEISOLATE_CONSIDER_TIME=1/g' "$CONFIG_FILE"

echo "Terminating standalone PDR process"
pkill -0 isolation_algo.py && pkill -9 -f isolation_algo.py 2>/dev/null
sleep 10

echo "Starting standalone PDR process"
python $PLUGIN_DIR/ufm_sim_web_service/isolation_algo.py >/dev/null 2>&1 &
#