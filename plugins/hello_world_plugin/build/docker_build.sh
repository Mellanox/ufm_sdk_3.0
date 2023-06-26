#!/bin/bash

set -eE

if [ "$EUID" -ne 0 ]
  then echo "Please run the script as root"
  exit
fi

SCRIPT_DIR="$(dirname "$(readlink -f "$0")")"
PARENT_DIR=$(realpath "${SCRIPT_DIR}/../../../")

PLUGIN_NAME=hello_world
IMAGE_NAME="ufm-plugin-${PLUGIN_NAME}"
IMAGE_VERSION=$1
OUT_DIR=$2
RANDOM_HASH=$3

echo "RANDOM_HASH  : [${RANDOM_HASH}]"
echo "SCRIPT_DIR   : [${SCRIPT_DIR}]"
echo " "
echo "IMAGE_VERSION: [${IMAGE_VERSION}]"
echo "IMAGE_NAME   : [${IMAGE_NAME}]"
echo "OUT_DIR      : [${OUT_DIR}]"
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
    prefix="mellanox"

    echo "build_docker_image"
    echo "  build_dir     : [${build_dir}]"
    echo "  image_name    : [${image_name}]"
    echo "  image_version : [${image_version}]"
    echo "  random_hash   : [${random_hash}]"
    echo "  out_dir       : [${out_dir}]"
    echo "  keep_image    : [${keep_image}]"
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

    echo "docker build --network host --no-cache --pull -t ${image_with_prefix_and_version} . --compress --build-arg PLUGIN_NAME=${PLUGIN_NAME}"

    docker build --network host --no-cache --pull -t ${image_with_prefix_and_version} . --compress --build-arg PLUGIN_NAME=${PLUGIN_NAME}
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

    echo "docker save ${image_with_prefix_and_version} | gzip > ${out_dir}/${full_image_version}-docker.img.gz"
    docker save ${image_with_prefix_and_version} | gzip > ${out_dir}/${full_image_version}-docker.img.gz
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

echo ${IMAGE_VERSION} > ../../${PLUGIN_NAME}_plugin/version

BUILD_DIR=$(create_out_dir)
cp Dockerfile ${BUILD_DIR}
cp -r ../../../utils ${BUILD_DIR}
cp -r ../../${PLUGIN_NAME}_plugin ${BUILD_DIR}

echo "BUILD_DIR    : [${BUILD_DIR}]"

build_docker_image $BUILD_DIR $IMAGE_NAME $IMAGE_VERSION $OUT_DIR ${RANDOM_HASH}
exit_code=$?
rm -rf ${BUILD_DIR}
popd
exit $exit_code