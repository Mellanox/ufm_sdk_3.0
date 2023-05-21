#!/bin/bash -x
# Executing script for debug
#\cp /auto/UFM/tmp/GVVM_CI/* .ci/
cd .ci
printenv
env

# Declare an array with plugin names
plugins=("UFM_NDT_Plugin" "snmp_receiver_plugin" "grpc_streamer_plugin" "sysinfo_plugin")
# Declare a variable for the common path
path_to_yaml="../plugins/%s/.ci/ci_matrix.yaml"
changed_files=$(git diff --name-only remotes/origin/$ghprbTargetBranch)
total=$(echo "$changed_files" | grep -v .gitmodules | wc -l)
# Loop over the plugins array
for plugin in "${plugins[@]}"; do
    plugin_changes=$(echo "$changed_files" | grep "$plugin" | grep -v .gitmodules | wc -l)
    if [ "$plugin_changes" -eq "$total" ] && [ "$total" -ne 0 ]; then
        ln -snf $(printf "$path_to_yaml" "$plugin") matrix_job_ci.yaml
        exit 0
    fi
done
# If no specific plugin changes were found
ln -snf ci_matrix.yaml matrix_job_ci.yaml
