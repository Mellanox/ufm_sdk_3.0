#!/bin/bash

set -eE

# install bright python API
SRC_DIR_PATH=/opt/ufm/ufm_plugin_bright/bright_plugin
PYTHON_PACKAGES_PATH=$(python3.9 -c 'import site; print(site.getsitepackages()[0])')
mv $SRC_DIR_PATH/src/bright/pythoncm.tar.gz ${PYTHON_PACKAGES_PATH}
tar -xf ${PYTHON_PACKAGES_PATH}/pythoncm.tar.gz -C ${PYTHON_PACKAGES_PATH}
rm -rf ${PYTHON_PACKAGES_PATH}/pythoncm.tar.gz

exit 0