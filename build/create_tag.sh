#!/bin/bash -x
#
# Copyright (C) 2013-2024 NVIDIA CORPORATION & AFFILIATES. ALL RIGHTS RESERVED.
#
# This software product is a proprietary product of Nvidia Corporation and its affiliates
# (the "Company") and all right, title, and interest in and to the software
# product, including all associated intellectual property rights, are and
# shall remain exclusively with the Company.
#
# This software product is governed by the End User License Agreement
# provided with the software product.
#

message_exit() {
	echo
	echo $1
	echo -n "ERROR: " >> ${logfile}
	echo $1 >> ${logfile}
	date >> ${logfile}
	\rm -Rf $tmp_repository_dir
	exit 1
}

message_log() {
	echo $1 | tee -a ${logfile}
}

get_opts() {
	while getopts :t:b:T:h o; do
		case "$o" in
		t) BUILD_TAG="$OPTARG";;
		b) BRANCH_NAME="$OPTARG";;
		T) MASTER_BUILD_TAG="$OPTARG";;
		*) usage;;
		esac
	done
}

usage () {
	echo "Usage: "
	echo -e " Run $basename [-b <branch> -t <UFM tag> ] [-T <UFM tag>]"
	echo -e " -b     Branch name"
	echo -e " -t     UFM tag"
	echo -e " -T     UFM build tag"
	echo -e " -h     Show help"
	echo -e "\nExamples:"
	echo -e " $basename -b main -t UFM_6_14_1_2"
	echo -e " $basename -T UFM_6_14_1_2"
	exit 1
}


basename=`basename $0`
get_opts $*

[ -z "$MASTER_BUILD_TAG" ] && ([ -z "$BUILD_TAG" ] || [ -z "$BRANCH_NAME" ]) && usage
[ ! -z "$MASTER_BUILD_TAG" ] && ([ ! -z "$BUILD_TAG" ] || [ ! -z "$BRANCH_NAME" ]) && usage
[ ! -z "$BUILD_TAG" ] && [ -z "$BRANCH_NAME" ] && usage
[ -z "$BUILD_TAG" ] && [ ! -z "$BRANCH_NAME" ] && usage


export YDMHMS=`\date "+%Y%m%d-%H%M%S"`
export logfile=/tmp/${basename}_${YDMHMS}.log

RUNNING_DIR=`dirname $0`
RUNNING_DIR=`cd $RUNNING_DIR; pwd`
. $RUNNING_DIR/common_release

#================================================
# Evaluate build tag
#================================================

if [ ! -z "$MASTER_BUILD_TAG" ]
    then
        BUILD_TAG="$MASTER_BUILD_TAG"
fi
evaluate_build_tag $BUILD_TAG

#================================================
# Checkout branch
#================================================
tmp_repository_dir=/tmp/sdk_build_tmp
git_init $tmp_repository_dir
git_conf
if [ ! -z "$MASTER_BUILD_TAG" ]
    then
        git_checkout_tag $MASTER_BUILD_TAG
    else
        git_checkout_branch $BRANCH_NAME
fi

#================================================
# Create build tag
#================================================
[ -z "$MASTER_BUILD_TAG" ] && git_finally $BRANCH_NAME $BUILD_TAG

message_log "Tag $BUILD_TAG created successfully"

exit 0
