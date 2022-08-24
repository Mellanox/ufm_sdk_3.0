#!/bin/bash -x
cd plugins/UFM_NDT_Plugin/.ci
printenv
env
#UPDATE softlink according to git changes
# changed_files=$(git diff --name-only remotes/origin/$ghprbTargetBranch)
total=$(git diff --name-only remotes/origin/$ghprbTargetBranch |grep UFM_NDT_Plugin |grep -v .gitmodules |wc -l)
webui=$(git diff --name-only remotes/origin/$ghprbTargetBranch |grep -v .gitmodules |wc -l)
if [ $webui -eq $total ]; then
    ln -snf ndt_plugin_ci.yaml ci_matrix.yaml
else
    ln -snf ndt_plugin_ci.yaml ci_matrix.yaml
fi