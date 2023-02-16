#!/bin/bash -x
# Executing script for debug
#\cp /auto/UFM/tmp/GVVM_CI/* .ci/
cd .ci
printenv
env

#UPDATE softlink according to git changes

changed_files=$(git diff --name-only remotes/origin/$ghprbTargetBranch)
echo "------------------------------"
UFM_NDT_Plugin=$(git diff --name-only remotes/origin/$ghprbTargetBranch | grep UFM_NDT_Plugin |grep -v .gitmodules |wc -l)
snmp_receiver_plugin=$(git diff --name-only remotes/origin/$ghprbTargetBranch | grep snmp_receiver_plugin |grep -v .gitmodules |wc -l)
grpc_streamer_plugin=$(git diff --name-only remotes/origin/$ghprbTargetBranch | grep grpc_streamer_plugin |grep -v .gitmodules |wc -l)
total=$(git diff --name-only remotes/origin/$ghprbTargetBranch |grep -v .gitmodules |wc -l)
if [ $UFM_NDT_Plugin -eq $total ] && [ $total -ne 0 ]; then
    ln -snf ../plugins/UFM_NDT_Plugin/.ci/ci_matrix.yaml matrix_job_ci.yaml
elif [ $snmp_receiver_plugin -eq $total ] && [ $total -ne 0 ]; then
    ln -snf ../plugins/snmp_receiver_plugin/.ci/ci_matrix.yaml matrix_job_ci.yaml
elif [ $grpc_streamer_plugin -eq $total ] && [ $total -ne 0 ]; then
    ln -snf ../plugins/grpc_streamer_plugin/.ci/ci_matrix.yaml matrix_job_ci.yaml
else
    ln -snf ci_matrix.yaml matrix_job_ci.yaml
fi
