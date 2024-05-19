#!/bin/bash -x

PLUGIN_DIR="plugins/pdr_deterministic_plugin"
pip install -r $PLUGIN_DIR/requirements.txt

start_simulation_server_pytest() {
    sudo -s
    cp -r utils $PLUGIN_DIR/tests
    CONFIG_FILE="/config/pdr_deterministic.conf"
    mkdir -p /config
    cp -f $PLUGIN_DIR/build/config/pdr_deterministic.conf "$CONFIG_FILE"
    sed -i -e 's/\nTEST_MODE=True\n//g' "$CONFIG_FILE"
    echo -e '\n[Common]\nTEST_MODE=True\n' >> "$CONFIG_FILE"
    sed -i -e 's/DRY_RUN=False/DRY_RUN=True/g' "$CONFIG_FILE"
    sed -i -e 's/INTERVAL=300/INTERVAL=10/g' "$CONFIG_FILE"
    sed -i -e 's/CONFIGURED_TEMP_CHECK=False/CONFIGURED_TEMP_CHECK=True/g' "$CONFIG_FILE"
    sed -i -e 's/DEISOLATE_CONSIDER_TIME=5/DEISOLATE_CONSIDER_TIME=1/g' "$CONFIG_FILE"

    echo "Starting 'isolation_algo.py'"
    python $PLUGIN_DIR/ufm_sim_web_service/isolation_algo.py &
}

start_pdr_standalone_pytest() {
    sudo -s
    cp -r utils $PLUGIN_DIR/ufm_sim_web_service
    echo "Starting 'simulation_telemetry.py'"
    python $PLUGIN_DIR/tests/simulation_telemetry.py
}

kill_simulation_server_pytest() {
    sudo -s
    echo "Terminating 'isolation_algo.py'"
    pkill -9 -f isolation_algo.py 2>/dev/null || true
}
