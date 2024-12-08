#!/bin/bash -x
git config --global safe.directory "$WORKSPACE"
cd .ci
# You can print specific environment variables here if required

# Get the list of changed files
changed_files=$(git diff --name-only remotes/origin/$ghprbTargetBranch)

# Check for changes excluding .gitmodules and root .ci directory
changes_excluding_gitmodules_and_root_ci=$(echo "$changed_files" | grep -v -e '.gitmodules' -e '^scripts/' -e '.gitignore' -e '^\.ci/' -e '^\.github/workflows' -e '\utils' -e '\plugins/ufm_log_analyzer_plugin') #Removing ufm_log_analyzer_plugin as for now it does not need a formal build

# Check if changes exist and only in a single plugin directory (including its .ci directory)
if [ -n "$changes_excluding_gitmodules_and_root_ci" ] && [ $(echo "$changes_excluding_gitmodules_and_root_ci" | cut -d '/' -f1,2 | uniq | wc -l) -eq 1 ]; then
    # Get the plugin directory name
    plugin_dir_name=$(echo "$changes_excluding_gitmodules_and_root_ci" | cut -d '/' -f1,2 | uniq)

    # Check if the plugin's CI file exists
    if [ -f "../$plugin_dir_name/.ci/ci_matrix.yaml" ]; then
        # Create symbolic link to the plugin's CI file
        ln -snf ../$plugin_dir_name/.ci/ci_matrix.yaml matrix_job_ci.yaml
    else
        # Print error message and exit with error status
        echo "Error: CI configuration file for $plugin_dir_name not found."
        exit 1
    fi
else
    # Check if the default CI file exists
    if [ -f "ci_matrix.yaml" ]; then
        # Create symbolic link to the default CI file
        ln -snf ci_matrix.yaml matrix_job_ci.yaml
    else
        # Print error message and exit with error status
        echo "Error: Default CI configuration file not found."
        exit 1
    fi
fi
