#!/bin/bash -x
# Executing script for debug
#\cp /auto/UFM/tmp/GVVM_CI/* .ci/
cd .ci
printenv
env
export conf_file=.ci/ci_matrix.yaml
#UPDATE softlink according to git changes
# changed_files=$(git diff --name-only remotes/origin/$ghprbTargetBranch)
# appliance=$(git diff --name-only remotes/origin/$ghprbTargetBranch |grep ufm_appliance |grep -v .gitmodules |wc -l)
# total=$(git diff --name-only remotes/origin/$ghprbTargetBranch |grep -v .gitmodules |wc -l)
# if [ $appliance -eq $total ] && [ $total -ne 0 ]; then
#     ln -snf matrix_job_appliance_ci.yaml matrix_job_ci.yaml
# else
#     ln -snf matrix_job_runci.yaml matrix_job_ci.yaml
# fi