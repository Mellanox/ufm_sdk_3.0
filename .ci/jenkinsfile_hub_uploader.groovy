pipeline{
    agent {
        docker {
            // if the docker file changes it should be build and uploaded manually
            image 'harbor.mellanox.com/swx-storage/ci-demo/x86_64/swx-dockerhub-uploader:20240221'
            label 'DOCKER'
            args '-v /auto/mswg:/auto/mswg -v /mswg:/mswg -v /var/run/docker.sock:/var/run/docker.sock --privileged'
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
                withCredentials([usernamePassword(credentialsId: '0fbf63c0-4a61-4543-811d-a182df47711b', usernameVariable: 'DH_USER', passwordVariable: 'DH_TOKEN' )]){
                    wrap([$class: 'BuildUser']) {
                        sh '''#!/bin/bash
                        authorized_users=( "bitkin" "afok" "kobib" "drorl" "tlerner" "omarj" "samerd" "atolikin" "atabachnik" "eylonk" "lennyv" )
                        if [[ ! "${authorized_users[*]}" == *"${BUILD_USER_ID}"* ]]; then
                            echo "${BUILD_USER_ID} not authorized to upload images to docker hub"
                            exit 1
                        fi'''
                    }
                    sh '''#!/bin/bash -xveE
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
                    '''
                }
            }
        }
    }
}