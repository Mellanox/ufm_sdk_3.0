#!/bin/bash

set -eE

if [ "$EUID" -ne 0 ]
  then echo "Please run the script as root"
  exit
fi

SCRIPT_DIR="$(dirname "$(readlink -f "$0")")"

IMAGE_VERSION=$1
IMAGE_NAME=ufm-plugin-ufm-rest
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

function create_out_dir()
{
    build_dir=$(mktemp --tmpdir -d ufm-plugin-ufm-rest_output_XXXXXXXX)
    chmod 777 ${build_dir}
    echo ${build_dir}
}

function build_docker_image()
{
    build_dir=$1
    image_name=$2
    image_version=$3
    random_hash=$4
    out_dir=$5
    keep_image=$6

    echo "build_docker_image"
    echo "  build_dir     : [${build_dir}]"
    echo "  image_name    : [${image_name}]"
    echo "  image_version : [${image_version}]"
    echo "  random_hash   : [${random_hash}]"
    echo "  out_dir       : [${out_dir}]"
    echo "  keep_image    : [${keep_image}]"
    echo " "
    if [ "${IMAGE_VERSION}" == "0.0.00-0" ]; then
        full_image_version="${image_name}_${image_version}-${random_hash}"
    else
        full_image_version="${image_name}"
    fi

    echo "  full_image_version    : [${full_image_version}]"

    pushd ${build_dir}
    echo "docker build --network host --no-cache --pull -t ${full_image_version} . --compress"

    docker build --network host --no-cache --pull -t ${full_image_version} . --compress
    exit_code=$?
    popd
    if [ $exit_code -ne 0 ]; then
        echo "Failed to build image"
        return $exit_code
    fi

    printf "\n\n\n"
    echo "docker images | grep ufm-plugin-ufm-plugin-ufm-rest"
    docker images | grep ufm-plugin-ufm-rest
    printf "\n\n\n"

    echo "docker save ${full_image_version}:latest | gzip > ${out_dir}/${full_image_version}.tar.gz"
    docker save ${full_image_version}:latest | gzip > ${out_dir}/${full_image_version}.tar.gz
    exit_code=$?
    if [ $exit_code -ne 0 ]; then
        echo "Failed to save image"
        return $exit_code
    fi
    if [ "$keep_image" != "y" -a "$keep_image" != "Y" ]; then
        docker image rm -f ${full_image_version}
    fi
    return 0
}

pushd ${SCRIPT_DIR}

BUILD_DIR=$(create_out_dir)

cp Dockerfile ${BUILD_DIR}
cp -r src ${BUILD_DIR}
cp -r lib ${BUILD_DIR}
cp -r whl ${BUILD_DIR}
cp init.sh ${BUILD_DIR}

echo "BUILD_DIR    : [${BUILD_DIR}]"

build_docker_image $BUILD_DIR $IMAGE_NAME $IMAGE_VERSION ${RANDOM_HASH} $OUT_DIR
exit_code=$?
rm -rf ${BUILD_DIR}
popd
exit $exit_code
