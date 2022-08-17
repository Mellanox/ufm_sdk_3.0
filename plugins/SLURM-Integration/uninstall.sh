#!/bin/bash
#
# Copyright © 2019-2021 NVIDIA CORPORATION & AFFILIATES. ALL RIGHTS RESERVED.
#
# This software product is a proprietary product of Nvidia Corporation and its affiliates
# (the "Company") and all right, title, and interest in and to the software
# product, including all associated intellectual property rights, are and
# shall remain exclusively with the Company.
#
# This software product is governed by the End User License Agreement
# provided with the software product.
#

SLURM_SERVICE_PATH='/lib/systemd/system/slurmctld.service'
SLURM_NOT_INSTALLED='SLURM is not installed. Please run the uninstaller on a SLURM controller.'
UNINSTALLING_PLUGIN='--Uninstalling UFM-SLURM integration plugin--'
UNINSTALLATION_COMPLETED_SUCCESSFULLY='Uninstallation completed successfully'
RM_FILES='Removing integration files...'
RM_CONF_SETTINGS='Removing configurations...'
UNINSTALLATION_FAILED='Uninstallation failed'
CONF_SETTINGS='Backup and remove configurations...'
RESTORE_BACKUP='There is a backup slurm config file before installation:'
RESTORE_BACKUP_CONFIRM='Do you want to restore it?'
uninstall_status=0


function remove_integration_files()
{
    declare -a intg_files=("ufm_slurm_epilog.py*" "ufm_slurm_prolog.py*" "ufm_slurm_utils.py*" "ufm_slurm.conf" "ufm-epilog.sh" "ufm-prolog.sh" "ufm_slurm_base.py*" "ufm_slurm*.log")
    for file in "${intg_files[@]}"
    do
    sudo rm -rf $file
    check_failure $? "Error while removing integration files"
    done

}

function update_slurm_conf()
{
    CONFIG_FILE="slurm.conf"
    # Backup the slurm conf file and remove configurations.
    sudo sed -i".uninstall.bak.`date \"+%Y%m%d_%H%M%S\"`" '/PrologSlurmctld/d' $CONFIG_FILE
    check_failure $? "Error while taking a backup for slurm.conf file"
    sudo sed -i '/EpilogSlurmctld/d' $CONFIG_FILE
    check_failure $? "Error while revert EpilogSlurmctld conf attribute"
}

function validate_requirements()
{
    # Check if script is running on SLURM controller
    if [ ! -f "$SLURM_SERVICE_PATH" ]; then
        failure "$SLURM_NOT_INSTALLED"
    fi

}

function ask_restore_backup()
{

    echo "$RESTORE_BACKUP"
    file=$(find $SLURM_DIR/slurm.conf.orig.* -printf '%T+ %p\n' | sort -r | head -n1 | cut -f 2 -d " " )

    if [ -z "$file" ]; then
        return
    fi
    echo $file
    echo "$RESTORE_BACKUP_CONFIRM"
    select yn in "Yes" "No"; do
    case $yn in
        Yes ) yes | sudo cp $file "slurm.conf"; break;;
        No ) return;;
    esac
    done
}


function failure()
{
    echo "$1"
    echo $UNINSTALLATION_FAILED
    exit 1
}

function check_failure()
{
    local sts=$1
    uninstall_status=$((uninstall_status + sts))
    if [ ! $uninstall_status -eq 0 ]; then
    failure "$2"
fi
}
#=======================================================================#
#main:
echo $UNINSTALLING_PLUGIN
echo "Please wait..."
validate_requirements
SLURM_DIR=$(dirname "$(cat $SLURM_SERVICE_PATH | grep ConditionPathExists | cut -d '=' -f2)")
BACKUP_UINSTALL_DONE="A copy of the slurm configuration is created before uninstallation on: $SLURM_DIR"
echo $RM_FILES
cd $SLURM_DIR;
remove_integration_files
echo $CONF_SETTINGS
ask_restore_backup
update_slurm_conf
echo $BACKUP_UINSTALL_DONE
echo $UNINSTALLATION_COMPLETED_SUCCESSFULLY
exit $uninstall_status
