# Declare an array with plugin names
plugins=("UFM_NDT_Plugin" "snmp_receiver_plugin" "grpc_streamer_plugin" "sysinfo_plugin")

# Declare a variable for the common path
path_to_yaml="../plugins/%s/.ci/ci_matrix.yaml"

changed_files=$(git diff --name-only remotes/origin/$ghprbTargetBranch)

# Initialize variable to track if any plugin had changes
plugin_had_changes=0

# Loop over the plugins array
for plugin in "${plugins[@]}"; do
    plugin_changes=$(echo "$changed_files" | grep "$plugin" | grep -v .gitmodules | wc -l)
    if [ "$plugin_changes" -gt 0 ]; then
        ln -snf $(printf "$path_to_yaml" "$plugin") matrix_job_ci.yaml
        plugin_had_changes=1
    fi
done

# If no specific plugin changes were found
if [ "$plugin_had_changes" -eq 0 ]; then
    ln -snf ci_matrix.yaml matrix_job_ci.yaml
fi
