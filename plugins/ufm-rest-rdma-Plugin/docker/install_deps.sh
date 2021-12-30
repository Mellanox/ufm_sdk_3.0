#!/bin/bash -eE


TMP_DIR=/tmp/sr_build_tmp/src
LIB_FILE_NAME=libservice_record_wrapper.so


usage()
{
    echo "Usage: "
    echo -e "  Run $0 to start compile service record library\n"
    echo -e "\nExamples:"
    echo -e " $0 [path_to_sources_directory] [path_to_directory_to_store result]"
    echo -e " $0 # in this case will be taken defaul values relativelly to script location"
}

if [ $# -eq 0 ];
then
   SCRIPT_DIR="$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
   echo "Destination and source directories will set relativelly to script location"
   src_dir=$SCRIPT_DIR/../src/service_record/
   dest_dir=$SCRIPT_DIR/../src/ufm_rdma/
else
    if [ ! $# -eq 2 ];
    then
        echo "Please ented path to service record source directory and to path where to copy compiled results"
        usage
        exit 1
    fi
    src_dir=$1
    dest_dir=$2
fi

if [ ! -d $dest_dir ]; then
    mkdir -p $dest_dir > /dev/null 2>&1 
    [ $? -ne 0 ] && { echo "Failed to create destination directory"; exit 1; }
fi

mkdir -p $TMP_DIR > /dev/null 2>&1
[ $? -ne 0 ] && { echo "Failed to create tmp build $TMP_DIR directory"; exit 1; }

# copy source code into build directory
cp -rf $src_dir $TMP_DIR
[ $? -ne 0 ] && { echo "Failed to copy SR sources to $TMP_DIR directory"; exit 1; }

# copy common code into build directory
cp -rf $src_dir/../common $TMP_DIR
[ $? -ne 0 ] && { echo "Failed to copy common dir to $TMP_DIR directory"; exit 1; }

cd $TMP_DIR/service_record

# build
make clean > /dev/null 2>&1
# build
make > /dev/null 2>&1 
[ $? -ne 0 ] && { echo "Failed to build SR lib"; exit 1; }
# check file created
[ ! -f $LIB_FILE_NAME ] && { echo "$LIB_FILE_NAME not found"; exit 1; }
#copy file
cp -f $LIB_FILE_NAME $dest_dir
[ $? -ne 0 ] && { echo "Failed to copy $LIB_FILE_NAME to $dest_dir "; exit 1; }

echo "SR lib file created and copied to $dest_dir"
exit 0
