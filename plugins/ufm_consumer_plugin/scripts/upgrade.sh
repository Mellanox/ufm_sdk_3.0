#!/bin/bash

CURRENT_CONF_FILE=/config/gv.cfg
NEW_CONF_FILE=/opt/ufm/files/conf/gv.cfg.org
TMP_CONF_FILE=/tmp/gv_tmp.cfg

. /opt/ufm/venv_ufm/bin/activate
python3 /opt/ufm/gvvm/infra/cfg_files_merge.pyc "${NEW_CONF_FILE}" "${CURRENT_CONF_FILE}" "${TMP_CONF_FILE}"

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
       echo  "Failed to merge old and new gv.cfg files. Merge result ${TMP_CONF_FILE} file not exist"
       status=1
    fi
else
    echo "An error occurred during merging the new and the current configurations"
fi

exit "${status}"