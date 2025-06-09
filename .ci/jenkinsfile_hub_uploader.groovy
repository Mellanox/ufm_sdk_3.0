pipeline{
    agent {
        docker {
            // if the docker file changes it should be build and uploaded manually
            image 'harbor.mellanox.com/ufm/ci/swx-dockerhub-uploader:20250427'
            label 'DOCKER'
            args '-v /auto/mswg:/auto/mswg -v /auto/sw/:/auto/sw -v /mswg:/mswg -v /var/run/docker.sock:/var/run/docker.sock --privileged'
        }
    }
    stages {
        stage('SCM') {
            steps {
                checkout scm
            }
        }
        stage('Upload to docker-hub'){
            steps{
                script {
                    withCredentials([usernamePassword(credentialsId: '0fbf63c0-4a61-4543-811d-a182df47711b', usernameVariable: 'DH_USER', passwordVariable: 'DH_TOKEN' )]){
                        wrap([$class: 'BuildUser']) {
                            def authorized_users = ["bitkin", "afok", "kobib", "drorl", "tlerner", "omarj", "samerd", "atolikin", "atabachnik", "eylonk", "lennyv", "asafb", "sspormas", "mkianovsky", "asafb", "samerd", "anana"]
                            def BUILD_USER_ID = env.BUILD_USER_ID.tokenize("@")[0]
                            if (!authorized_users.contains(BUILD_USER_ID)) {
                                error """${BUILD_USER_ID} is not authorized to upload images to Docker Hub.
    Please contact one of the approved users to upload a container: ${authorized_users.join(', ')}"""
                            }
                        }
                        sh '''#!/bin/bash -xv
                        printenv
                        cmd_args=''
                        if [ -n "${IMAGE_NAME}" ]; then
                            cmd_args="${cmd_args}-i ${IMAGE_NAME} "
                        fi
                        if [ -n "${IMAGE_TAG}" ]; then
                            cmd_args="${cmd_args}-t ${IMAGE_TAG} "
                        fi
                        if [ "${FORCE_PUSH}" == "true" ]; then
                            cmd_args="${cmd_args}-f "
                        fi
                        if [ "${LATEST}" == "true" ]; then
                            cmd_args="${cmd_args}-l "
                        fi
                        python3 .ci/dockerhub_uploader.py -u ${DH_USER} -p ${DH_TOKEN} -d ${IMAGE_PATH} ${cmd_args}
                        status=$?
                        if [ ${status} -ne 0 ]; then
                            echo "Failed to upload image ${IMAGE_PATH} to Docker Hub"
                            exit ${status}
                        else
                            echo "Successfully uploaded image ${IMAGE_PATH} to Docker Hub"
                            exit 0
                        fi
                        '''
                    }
                }
            }
        }
    }
}
