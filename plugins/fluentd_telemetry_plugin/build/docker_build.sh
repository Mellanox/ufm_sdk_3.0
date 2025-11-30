#!/bin/bash

set -eE

if [ "$EUID" -ne 0 ]
  then echo "Please run the script as root"
  exit
fi

SCRIPT_DIR="$(dirname "$(readlink -f "$0")")"

PLUGIN_NAME=tfs
IMAGE_NAME="ufm-plugin-${PLUGIN_NAME}"
IMAGE_VERSION=$1
OUT_DIR=$2
RANDOM_HASH=$3
DEV_TOOLS=${DEV_TOOLS:-0}

echo "RANDOM_HASH  : [${RANDOM_HASH}]"
echo "SCRIPT_DIR   : [${SCRIPT_DIR}]"
echo " "
echo "IMAGE_VERSION: [${IMAGE_VERSION}]"
echo "IMAGE_NAME   : [${IMAGE_NAME}]"
echo "OUT_DIR      : [${OUT_DIR}]"
echo "DEV_TOOLS    : [${DEV_TOOLS}]"
echo " "

if [ -z "${OUT_DIR}" ]; then
    OUT_DIR="."
fi
if [ -z "${IMAGE_VERSION}" ]; then
    IMAGE_VERSION="latest"
fi

function create_out_dir()
{
    build_dir=$(mktemp --tmpdir -d ${IMAGE_NAME}_output_XXXXXXXX)
    chmod 777 ${build_dir}
    echo ${build_dir}
}

function build_docker_image()
{
    build_dir=$1
    image_name=$2
    image_version=$3
    out_dir=$4
    random_hash=$5
    keep_image=$6
    dev_tools=${7:-0}
    prefix="mellanox"

    echo "build_docker_image"
    echo "  build_dir     : [${build_dir}]"
    echo "  image_name    : [${image_name}]"
    echo "  image_version : [${image_version}]"
    echo "  random_hash   : [${random_hash}]"
    echo "  out_dir       : [${out_dir}]"
    echo "  keep_image    : [${keep_image}]"
    echo "  dev_tools     : [${dev_tools}]"
    echo "  prefix        : [${prefix}]"
    echo " "
    if [ "${IMAGE_VERSION}" == "0.0.00-0" ]; then
        full_image_version="${image_name}_${image_version}-${random_hash}"
    else
        full_image_version="${image_name}_${image_version}"
    fi

    echo "  full_image_version    : [${full_image_version}]"

    image_with_prefix="${prefix}/${image_name}"
    image_with_prefix_and_version="${prefix}/${image_name}:${image_version}"

    pushd ${build_dir}
    echo ${full_image_version} > version
    build_args="--build-arg DEV_TOOLS=${dev_tools}"
    echo "docker build --network host --no-cache --pull ${build_args} -t ${image_with_prefix_and_version} . --compress"

    docker build --network host --no-cache --pull ${build_args} -t ${image_with_prefix_and_version} . --compress
    exit_code=$?
    popd
    if [ $exit_code -ne 0 ]; then
        echo "Failed to build image"
        return $exit_code
    fi

    printf "\n\n\n"
    echo "docker images | grep ${image_with_prefix}"
    docker images | grep ${image_with_prefix}
    printf "\n\n\n"

    echo "docker save ${image_with_prefix_and_version} | gzip > ${out_dir}/${full_image_version}.tgz"
    docker save ${image_with_prefix_and_version} | gzip > ${out_dir}/${full_image_version}.tgz
    exit_code=$?
    if [ $exit_code -ne 0 ]; then
        echo "Failed to save image"
        return $exit_code
    fi
    if [ "$keep_image" != "y" -a "$keep_image" != "Y" ]; then
        docker image rm -f ${image_with_prefix_and_version}
    fi
    return 0
}

pushd ${SCRIPT_DIR}

BUILD_DIR=$(create_out_dir)
cp Dockerfile ${BUILD_DIR}

# Copy .dockerignore if it exists
if [ -f ".dockerignore" ]; then
    cp .dockerignore ${BUILD_DIR}
fi

# Copy utils - exclude tests and unnecessary files
mkdir -p ${BUILD_DIR}/utils
cp ../../../utils/__init__.py ${BUILD_DIR}/utils/ 2>/dev/null || true
cp ../../../utils/logger.py ${BUILD_DIR}/utils/
cp ../../../utils/utils.py ${BUILD_DIR}/utils/
cp ../../../utils/config_parser.py ${BUILD_DIR}/utils/
cp ../../../utils/json_schema_validator.py ${BUILD_DIR}/utils/
cp ../../../utils/args_parser.py ${BUILD_DIR}/utils/
cp ../../../utils/exception_handler.py ${BUILD_DIR}/utils/
cp ../../../utils/ufm_rest_client.py ${BUILD_DIR}/utils/
cp -r ../../../utils/flask_server ${BUILD_DIR}/utils/
mkdir -p ${BUILD_DIR}/utils/fluentd
cp -r ../../../utils/fluentd/fluent ${BUILD_DIR}/utils/fluentd/

# Copy ufm_sdk_tools - only required modules
mkdir -p ${BUILD_DIR}/ufm_sdk_tools/src
cp ../../../ufm_sdk_tools/__init__.py ${BUILD_DIR}/ufm_sdk_tools/ 2>/dev/null || true
cp ../../../ufm_sdk_tools/src/__init__.py ${BUILD_DIR}/ufm_sdk_tools/src/ 2>/dev/null || true
cp -r ../../../ufm_sdk_tools/src/utils ${BUILD_DIR}/ufm_sdk_tools/src/
cp -r ../../../ufm_sdk_tools/src/xdr_utils ${BUILD_DIR}/ufm_sdk_tools/src/
cp -r ../../../ufm_sdk_tools/src/config_parser_utils ${BUILD_DIR}/ufm_sdk_tools/src/

# Copy plugin - exclude venv, tests, pycache, docs
mkdir -p ${BUILD_DIR}/fluentd_telemetry_plugin
cp ../../fluentd_telemetry_plugin/__init__.py ${BUILD_DIR}/fluentd_telemetry_plugin/ 2>/dev/null || true
cp ../../fluentd_telemetry_plugin/requirements.txt ${BUILD_DIR}/fluentd_telemetry_plugin/
cp -r ../../fluentd_telemetry_plugin/src ${BUILD_DIR}/fluentd_telemetry_plugin/
cp -r ../../fluentd_telemetry_plugin/conf ${BUILD_DIR}/fluentd_telemetry_plugin/
cp -r ../../fluentd_telemetry_plugin/scripts ${BUILD_DIR}/fluentd_telemetry_plugin/
cp -r ../../fluentd_telemetry_plugin/lib ${BUILD_DIR}/fluentd_telemetry_plugin/

# Remove __pycache__ directories from build context
find ${BUILD_DIR} -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find ${BUILD_DIR} -type f -name "*.pyc" -delete 2>/dev/null || true

echo "BUILD_DIR    : [${BUILD_DIR}]"

build_docker_image $BUILD_DIR $IMAGE_NAME $IMAGE_VERSION $OUT_DIR ${RANDOM_HASH} "" ${DEV_TOOLS}
exit_code=$?
rm -rf ${BUILD_DIR}
popd
exit $exit_code
