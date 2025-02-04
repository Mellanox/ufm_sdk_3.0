#!/bin/bash

CURRENT_CONF_FILE=/config/ndt.conf
NEW_CONF_FILE=/opt/ufm/ufm_plugin_ndt/ndt.conf
TMP_CONF_FILE=/tmp/ndt_tmp.conf

python3 /opt/ufm/ufm_plugin_ndt/cfg_files_merge.py "${NEW_CONF_FILE}" "${CURRENT_CONF_FILE}" "${TMP_CONF_FILE}"

status=$?
# Check if the configurations upgrade was successful
if [ "${status}" -eq 0 ]; then
    echo "Configuration file upgraded successfully."
    echo "Copy upgraded file ${TMP_CONF_FILE} to initial location ${CURRENT_CONF_FILE}"
    if [ -f $TMP_CONF_FILE ]; then
        # new file created - move to the original
        \cp ${CURRENT_CONF_FILE} ${CURRENT_CONF_FILE}.old > /dev/null 2>&1
        \mv -f ${TMP_CONF_FILE} ${CURRENT_CONF_FILE} > /dev/null 2>&1
        status=$?
    else
       echo  "Failed to merge old and new ndt.conf file. Merge result ${TMP_CONF_FILE} file not exist"
       status=1
    fi
else
    echo "An error occurred during merging the new and the current configurations"
fi

exit "${status}"


