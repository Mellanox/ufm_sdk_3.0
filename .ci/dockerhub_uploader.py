#!/usr/bin/python3
import requests
import sys
import os
import docker
import argparse
import json
import tarfile


DEBUG=os.environ.get('DEBUG', None)

def log_error(message) -> None:
    """Helper method to print errors and exit."""
    if hasattr(sys.stderr, 'isatty') and sys.stderr.isatty():
        output = f'\033[0;31m-E- {message}\033[0m'
    else:
        output = message
    print(output, file=sys.stderr)
    sys.exit(1)


def log_warning(message) -> None:
    """Helper method to print warnings."""
    if hasattr(sys.stderr, 'isatty') and sys.stderr.isatty():
        output = f'\033[1;33m-W- {message}\033[0m'
    else:
        output = message
    print(output, file=sys.stderr)

def log_info(message) -> None:
    """Helper method to print info."""
    print(f'-I- {message}', file=sys.stdout)

def log_debug(message) -> None:
    """Helper method to print debug."""
    if DEBUG:
        print(f'-D- {message}', file=sys.stdout)


class DockerHubUploader:
    """
    Helper class to upload images to docker hub.
    
    Args:
        username (str): Docker hub username
        password (str): Docker hub password/access-token
    """
    DOCKERHUB_URL = r'https://hub.docker.com'
    DOCKERHUB_API_VER = '/v2'

    def __init__(self, username:str, password:str) -> None:
        self.username = username
        self.password = password
        self.session = requests.session()
        self.rate_limit = 0
        self.repository = 'mellanox'
        self.token = None
        self.client = docker.from_env()
        self.image = ""
        self.tag = ""
        self.image_path = ""

    def login(self) -> None:
        """Login to docker-hub used for validation of image tags"""
        log_debug('starting DockerHubUploader.login')
        url = self.DOCKERHUB_URL + self.DOCKERHUB_API_VER + '/users/login'
        data = {
            "username": self.username,
            "password": self.password
        }
        response = self.session.post(url=url, data=data)
        if response.status_code == 200 and 'token' in response.json():
            self.token = response.json()['token']
            log_info('Acquired Token successfully')
            log_debug(f'token:"{self.token}"')
        else:
            log_error(f'Could not acquire token from docker-hub, please verify user and credentials\n{response.text}')

    def parse_image_tags(self):
        """Helper function for parsing image name and tag from manifest"""
        # If image name and tag were passed to the object don't parse it from the metadata
        if self.image and self.tag:
            if '/' in self.image:
                self.repository = '/'.join(self.image.split('/')[:-1])
                self.image = self.image.split('/')[-1]
            return
        meta_data = None
        if not tarfile.is_tarfile(self.image_path):
            log_error(f'{self.image_path} is not a valid tar file')
        with tarfile.open(self.image_path, 'r') as t:
            # get the image manifest to determine image name and tag
            meta_data = json.load(t.extractfile(r'manifest.json'))
        if not meta_data:
            log_error(f"Could not extract manifest.json from {self.image_path}")
        try:
            # take the first tag of the first image, there should be only one anyway
            image_name = meta_data[0]['RepoTags'][0]
            # validate repo in image metadata
            if '/' in image_name:
                self.repository = '/'.join(image_name.split('/')[:-1])
                image_name = image_name.split('/')[-1]
            if not self.image:
                self.image = image_name.split(':')[0]
            if not self.tag:
                self.tag = image_name.split(':')[1]
            if self.tag == 'latest':
                log_error(f'Invalid tag "latest" for {self.image_path}, please use the --tag flag to override the tag to a proper version number')
        except KeyError:
            log_error(f"Could not extract image name / tag from manifest.json of {self.image_path}")

    def check_image_tag_docker_hub(self, tag=None) -> bool:
        """Validate if image tag already exists on Docker-Hub"""
        if not tag:
            tag = self.tag
        log_debug(f'starting DockerHubUploader.check_image_tag_docker_hub with image_name:"{self.image}",tag:"{tag}"')
        url = self.DOCKERHUB_URL + self.DOCKERHUB_API_VER + f'/repositories/{self.repository}/{self.image}/tags'
        head = {
            'Authorization': f'Bearer {self.token}'
        }
        # run in a loop over all tags to see if exists
        while True:
            response = self.session.get(url=url, headers=head)
            log_debug(f'get images status code:{response.status_code}')
            log_debug(f'get images request headers:{response.request.headers}')
            log_debug(f'get images request url:{response.request.url}')
            log_debug(f'get images response headers:{response.headers}')
            if response.status_code == 200:
                image_tags = response.json()
                for result in image_tags['results']:
                    if result['name'] == self.tag:
                        return True
            # image doesn't exist pushing new image
            elif response.status_code == 404:
                log_warning(f"{self.repository}/{self.image} was not found in docker hub creating a new repository")
                break
            else:
                log_error(f'Could not get info from Docker-Hub: return code:{response.status_code}\n{response.text}')
            if image_tags['next']:
                url = image_tags['next']
            else:
                log_info(f'Image: {self.repository}/{self.image}:{tag} was not found on docker hub.')
                break
        return False
    
    def _check_image_locally(self, tag=None) -> bool:
        """helper method to check if image already exists in local docker"""
        if not tag:
            tag = self.tag
        log_debug(f'starting DockerHubUploader._check_image_locally with image:"{self.image}",tag:"{tag}"')
        for img in self.client.images.list():
            for img_name in  img.attrs['RepoTags']:
                if img_name == f"{self.repository}/{self.image}:{tag}":
                    return True
        return False

    def _delete_image_locally(self, tag=None) -> None:
        """Helper method to remove images from local docker"""
        log_debug(f'starting DockerHubUploader._delete_image_locally with image:"{self.image}",tag:"{tag}"')
        if not tag:
            tag = self.tag
        try:
            self.client.images.remove(image=f'{self.repository}/{self.image}:{tag}', force=True)
        except Exception as e:
            log_error(f"could not remove {self.repository}/{self.image}:{tag}\n    {e}")

    def load_docker_img(self):
        """Load a docker file to docker engine"""
        log_debug(f'starting DockerHubUploader.load_docker_img with image:"{self.image}",tag:"{self.tag}", path:"{self.image_path}"')
        # Check if the image:tag already exists if so try to delete it.
        if self._check_image_locally():
            log_warning(f'{self.image}:{self.tag} was found locally removing it from docker engine.')
            try:
                self._delete_image_locally()
            except Exception as e:
                log_error(f'Could not delete {self.image}:{self.tag} from local docker.\n    {e}')
        if not os.path.exists(self.image_path):
            log_error(f'{self.image_path} doesn\'t exists.')
        with open(self.image_path, 'rb') as img:
            try:
                _ = self.client.images.load(img)
                log_info(f'Loaded {self.repository}/{self.image}:{self.tag} to local docker engine.')
            except Exception as e:
                log_error(f'Could not load the {self.repository}/{self.image}:{self.tag} to docker.\n    {e}')
                # tag as latest if latest flag exists

    def tag_image(self, new_tag):
        """Load a docker file to docker engine"""
        log_debug(f'starting DockerHubUploader.tag_image with image:"{self.image}",current_tag:"{self.tag}", new_tag:"{new_tag}"')
         # check if latest exists locally
        if self._check_image_locally(new_tag):
            log_warning(f'{self.repository}/{self.image}:{new_tag} was found locally removing it from docker engine.')
            try:
                self._delete_image_locally(self.image, new_tag)
            except Exception as e:
                log_error(f'Could not delete {self.repository}/{self.image}:{new_tag} from local docker.\n    {e}')
        try:
            img = self.client.images.get(f'{self.repository}/{self.image}:{self.tag}')
            img.tag(f'{self.repository}/{self.image}', new_tag)
            log_info(f'Tagged {self.repository}/{self.image}:{self.tag} as {self.repository}/{self.image}:{new_tag}.')
        except Exception as e:
            log_error(f'Could not tag {self.repository}/{self.image}:{self.tag} as {self.repository}/{self.image}:{new_tag}\n    {e}')

    def push_image(self,tag=None) -> None:
        """Push image to docker-hub"""
        if not tag:
            tag = self.tag
        log_debug(f'starting DockerHubUploader.push_image with image:"{self.image}"tag:"{tag}"')
        try:
            result = self.client.images.push(repository=f'{self.repository}/{self.image}', tag=tag,
                                              auth_config={'username': self.username, 'password': self.password},stream=True)
            for line in result:
                if 'error' in json.loads(line).keys():
                    log_error(f'Could not push {self.repository}/{self.image}:{tag}\nError from Docker:{line.decode("utf-8")}"')
                log_info(line.decode("utf-8"))
            log_info(f"{self.repository}/{self.image}:{tag} was pushed successfully")
        except Exception as e:
            log_error(f"Could not push {self.repository}/{self.image}:{tag} to Docker-Hub")

    def cleanup(self, tag=None):
        """Cleanup function to remove loaded docker images from host"""
        if self._check_image_locally(tag=tag):
            self._delete_image_locally(tag=tag)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(prog='dockerhub_uploader')
    parser.add_argument('-u', '--username', type=str, help='Username for Docker-Hub access, P.S. this user must have a write permission.')
    parser.add_argument('-p', '--password', type=str, help='Password/access-token for Docker-Hub access.')
    parser.add_argument('-i', '--image', type=str, help='Optional: override docker upload image name, must be in the format of repo/image e.g mellanox/ufm-enterprise.')
    parser.add_argument('-t', '--tag', type=str, help='Optional: override docker image tag.')
    parser.add_argument('-d', '--path', type=str, help='Path to docker image tar file.')
    parser.add_argument('-f', '--force', default=False, action='store_true', help='Force push the container to docker hub if the tag already exists, use with caution will override the image.')
    parser.add_argument('-l', '--latest', default=False, action='store_true', help='make the tag also latest.')
    args = parser.parse_args()
    if not args.username and not os.environ.get('DOCKERHUB_USER'):
        log_error("Docker-Hub username must be specified by using the -u/--username flags or by exporting \n    DOCKERHUB_USER=<username> environment variable from the shell.")
    if not args.password and not os.environ.get('DOCKERHUB_PASS'):
        log_error("Docker-Hub username must be specified by using the -p/--password flags or by exporting \n    DOCKERHUB_PASS=<password/access-token> environment variable from the shell.")
    if not args.path:
        log_error("Docker image path to tar file is not specified use the -d/--path flags to pass it to he script.")
    if args.force:
        log_warning("Using force push, if the image and tag exists on Docker-Hub it will be overwritten.")
    if args.latest:
        log_warning(f"latest tag will be uploaded in addition to normal tag.")

    dhu = DockerHubUploader(args.username, args.password)
    dhu.image_path = args.path
    if args.image:
        dhu.image = args.image
    if args.tag:
        dhu.tag = args.tag
    dhu.parse_image_tags()
    dhu.login()
    if dhu.check_image_tag_docker_hub() and not args.force:
        log_error(f'Image {dhu.image}:{dhu.tag} already exists on Docker-Hub.\n    in case you wish to overwrite it use the -f/--force flag to force push the image.')
    else:
        dhu.load_docker_img()
        dhu.push_image()
    if args.latest:
        dhu.tag_image('latest')
        dhu.push_image('latest')
        dhu.cleanup('latest')
    dhu.cleanup()