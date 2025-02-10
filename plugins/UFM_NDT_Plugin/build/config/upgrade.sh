#!/bin/bash

CURRENT_CONF_FILE=/config/ndt.conf
NEW_CONF_FILE=/opt/ufm/ufm_plugin_ndt/ndt.conf

\cp -f ${CURRENT_CONF_FILE} ${CURRENT_CONF_FILE}.old > /dev/null 2>&1

python3 /opt/ufm/ufm_plugin_ndt/ufm_sdk_tools/src/config_parser_utils/merge_configuration_files.py "${CURRENT_CONF_FILE}" "${NEW_CONF_FILE}"
status=$?
# Check if the configurations upgrade was successful
if [ "${status}" -eq 0 ]; then
    echo "Configuration file upgraded successfully."
else
    echo  "Failed to merge old and new ndt.conf file."
fi

exit "${status}"


