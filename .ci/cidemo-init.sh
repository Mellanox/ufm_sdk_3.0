#!/bin/bash -x
cd .ci
# You can print specific environment variables here if required

# Get the list of changed files
changed_files=$(git diff --name-only remotes/origin/$ghprbTargetBranch)

# Check for changes excluding .gitmodules
changes_excluding_gitmodules=$(echo "$changed_files" | grep -v .gitmodules)

# Check if changes exist and only in a single directory
if [ -n "$changes_excluding_gitmodules" ] && [ $(echo "$changes_excluding_gitmodules" | grep -o "/" | wc -l) -eq $(echo "$changes_excluding_gitmodules" | wc -l) ]; then
    # Get the directory name
    dir_name=$(echo "$changes_excluding_gitmodules" | cut -d '/' -f1)

    # Check if the directory's CI file exists
    if [ -f "../plugins/$dir_name/.ci/ci_matrix.yaml" ]; then
        # Create symbolic link to the directory's CI file
        ln -snf ../plugins/$dir_name/.ci/ci_matrix.yaml matrix_job_ci.yaml
    else
        # Print error message and exit with error status
        echo "Error: CI configuration file for $dir_name not found."
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
