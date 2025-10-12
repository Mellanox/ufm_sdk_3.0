pipeline {
    agent {
        docker {
            // Docker image with Docker-in-Docker support for manifest creation
            // If the docker file changes it should be built and uploaded manually
            image 'harbor.mellanox.com/ufm/ci/swx-dockerhub-uploader:20250427'
            label 'DOCKER'
            args '-v /auto/mswg:/auto/mswg -v /auto/sw/:/auto/sw -v /mswg:/mswg -v /var/run/docker.sock:/var/run/docker.sock --privileged'
        }
    }
    
    parameters {
        string(
            name: 'AMD_IMAGE_PATH',
            description: 'Path to the AMD64 Docker image tar file',
            defaultValue: ''
        )
        string(
            name: 'ARM_IMAGE_PATH',
            description: 'Path to the ARM64 Docker image tar file',
            defaultValue: ''
        )
        string(
            name: 'IMAGE_NAME',
            description: 'Base image name (without architecture suffix). Will create: {IMAGE_NAME}_amd, {IMAGE_NAME}_arm, and {IMAGE_NAME} (multi-arch)',
            defaultValue: ''
        )
        string(
            name: 'IMAGE_TAG',
            description: 'Image tag/version (e.g., v1.0.0, 1.2.3). Do not use "latest".',
            defaultValue: ''
        )
        string(
            name: 'REPOSITORY',
            description: 'Docker Hub repository name',
            defaultValue: 'mellanox'
        )
        booleanParam(
            name: 'FORCE_PUSH',
            description: 'Force push even if images already exist on Docker Hub (use with caution!)',
            defaultValue: false
        )
        booleanParam(
            name: 'LATEST',
            description: 'Also tag the images as "latest" in addition to the specified tag',
            defaultValue: false
        )
    }
    
    stages {
        stage('SCM') {
            steps {
                checkout scm
            }
        }
        
        stage('Validate Parameters') {
            steps {
                script {
                    // Validate required parameters
                    def errors = []
                    
                    if (!params.AMD_IMAGE_PATH?.trim()) {
                        errors.add('AMD_IMAGE_PATH is required')
                    }
                    if (!params.ARM_IMAGE_PATH?.trim()) {
                        errors.add('ARM_IMAGE_PATH is required')
                    }
                    if (!params.IMAGE_NAME?.trim()) {
                        errors.add('IMAGE_NAME is required')
                    }
                    if (!params.IMAGE_TAG?.trim()) {
                        errors.add('IMAGE_TAG is required')
                    }
                    
                    // Validate tag is not 'latest'
                    if (params.IMAGE_TAG?.trim() == 'latest') {
                        errors.add('IMAGE_TAG cannot be "latest". Use a version number and set LATEST=true if needed.')
                    }
                    
                    // Check if files exist
                    if (params.AMD_IMAGE_PATH && !fileExists(params.AMD_IMAGE_PATH)) {
                        errors.add("AMD image file not found: ${params.AMD_IMAGE_PATH}")
                    }
                    if (params.ARM_IMAGE_PATH && !fileExists(params.ARM_IMAGE_PATH)) {
                        errors.add("ARM image file not found: ${params.ARM_IMAGE_PATH}")
                    }
                    
                    if (errors) {
                        error "Parameter validation failed:\n  - ${errors.join('\n  - ')}"
                    }
                    
                    // Display configuration
                    echo """
=============================================================================
Multi-Architecture Docker Hub Upload Configuration
=============================================================================
AMD Image Path:  ${params.AMD_IMAGE_PATH}
ARM Image Path:  ${params.ARM_IMAGE_PATH}
Image Name:      ${params.IMAGE_NAME}
Image Tag:       ${params.IMAGE_TAG}
Repository:      ${params.REPOSITORY}
Force Push:      ${params.FORCE_PUSH}
Tag as Latest:   ${params.LATEST}

Will create the following repositories:
  1. ${params.REPOSITORY}/${params.IMAGE_NAME}_amd:${params.IMAGE_TAG}  (AMD64)
  2. ${params.REPOSITORY}/${params.IMAGE_NAME}_arm:${params.IMAGE_TAG}  (ARM64)
  3. ${params.REPOSITORY}/${params.IMAGE_NAME}:${params.IMAGE_TAG}      (Multi-Arch Manifest)
=============================================================================
"""
                }
            }
        }
        
        stage('Authorization Check') {
            steps {
                script {
                    wrap([$class: 'BuildUser']) {
                        def authorized_users = [
                            "bitkin", "afok", "kobib", "drorl", "tlerner", 
                            "omarj", "samerd", "atolikin", "atabachnik", 
                            "eylonk", "lennyv", "asafb", "sspormas", 
                            "mkianovsky", "anana"
                        ]
                        
                        def BUILD_USER_ID = env.BUILD_USER_ID?.tokenize("@")[0]
                        
                        if (!authorized_users.contains(BUILD_USER_ID)) {
                            error """
${BUILD_USER_ID} is not authorized to upload images to Docker Hub.

Please contact one of the approved users to upload a container:
${authorized_users.join(', ')}
"""
                        }
                        
                        echo "User ${BUILD_USER_ID} is authorized to upload images"
                    }
                }
            }
        }
        
        stage('Upload Multi-Arch Images') {
            steps {
                script {
                    withCredentials([
                        usernamePassword(
                            credentialsId: '0fbf63c0-4a61-4543-811d-a182df47711b',
                            usernameVariable: 'DH_USER',
                            passwordVariable: 'DH_TOKEN'
                        )
                    ]) {
                        sh '''#!/bin/bash -xv
                        set -e  # Exit on any error
                        
                        echo "==================================================================="
                        echo "Starting Multi-Architecture Docker Hub Upload"
                        echo "==================================================================="
                        
                        # Print environment for debugging
                        printenv | grep -E '(IMAGE_|REPOSITORY|FORCE|LATEST|PATH)' || true
                        
                        # Build command arguments
                        cmd_args=""
                        cmd_args="${cmd_args} --amd-path ${AMD_IMAGE_PATH}"
                        cmd_args="${cmd_args} --arm-path ${ARM_IMAGE_PATH}"
                        cmd_args="${cmd_args} -i ${IMAGE_NAME}"
                        cmd_args="${cmd_args} -t ${IMAGE_TAG}"
                        cmd_args="${cmd_args} -r ${REPOSITORY}"
                        
                        if [ "${FORCE_PUSH}" == "true" ]; then
                            cmd_args="${cmd_args} -f"
                            echo "WARNING: Force push is enabled!"
                        fi
                        
                        if [ "${LATEST}" == "true" ]; then
                            cmd_args="${cmd_args} -l"
                            echo "INFO: Will also tag as 'latest'"
                        fi
                        
                        # Enable Docker experimental features for manifest support
                        export DOCKER_CLI_EXPERIMENTAL=enabled
                        
                        # Login to Docker Hub for manifest commands
                        echo "Logging in to Docker Hub..."
                        echo "${DH_TOKEN}" | docker login -u "${DH_USER}" --password-stdin
                        
                        echo "==================================================================="
                        echo "Executing: python3 .ci/dockerhub_multiarch_uploader.py -u <USER> -p <TOKEN> ${cmd_args}"
                        echo "==================================================================="
                        
                        # Run the uploader script
                        python3 .ci/dockerhub_multiarch_uploader.py \\
                            -u "${DH_USER}" \\
                            -p "${DH_TOKEN}" \\
                            ${cmd_args}
                        
                        status=$?
                        
                        echo "==================================================================="
                        if [ ${status} -ne 0 ]; then
                            echo "ERROR: Failed to upload multi-arch images"
                            echo "==================================================================="
                            exit ${status}
                        else
                            echo "SUCCESS: Multi-arch images uploaded successfully!"
                            echo ""
                            echo "Uploaded images:"
                            echo "  - ${REPOSITORY}/${IMAGE_NAME}_amd:${IMAGE_TAG}"
                            echo "  - ${REPOSITORY}/${IMAGE_NAME}_arm:${IMAGE_TAG}"
                            echo "  - ${REPOSITORY}/${IMAGE_NAME}:${IMAGE_TAG} (multi-arch)"
                            if [ "${LATEST}" == "true" ]; then
                                echo "  - ${REPOSITORY}/${IMAGE_NAME}:latest (multi-arch)"
                            fi
                            echo "==================================================================="
                            exit 0
                        fi
                        '''
                    }
                }
            }
        }
    }
    
    post {
        success {
            echo """
╔═══════════════════════════════════════════════════════════════════════════╗
║                                                                           ║
║  ✓ Multi-Architecture Docker Hub Upload Completed Successfully!          ║
║                                                                           ║
║  AMD Image:      ${params.REPOSITORY}/${params.IMAGE_NAME}_amd:${params.IMAGE_TAG}
║  ARM Image:      ${params.REPOSITORY}/${params.IMAGE_NAME}_arm:${params.IMAGE_TAG}
║  Multi-Arch:     ${params.REPOSITORY}/${params.IMAGE_NAME}:${params.IMAGE_TAG}
║                                                                           ║
╚═══════════════════════════════════════════════════════════════════════════╝
"""
        }
        failure {
            echo """
╔═══════════════════════════════════════════════════════════════════════════╗
║                                                                           ║
║  ✗ Multi-Architecture Docker Hub Upload Failed                           ║
║                                                                           ║
║  Please check the logs above for error details.                          ║
║                                                                           ║
╚═══════════════════════════════════════════════════════════════════════════╝
"""
        }
    }
}




