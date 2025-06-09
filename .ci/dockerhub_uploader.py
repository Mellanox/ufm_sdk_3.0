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
    print(output, file=sys.stderr, flush=True)
    sys.exit(1)


def log_warning(message) -> None:
    """Helper method to print warnings."""
    if hasattr(sys.stderr, 'isatty') and sys.stderr.isatty():
        output = f'\033[1;33m-W- {message}\033[0m'
    else:
        output = message
    print(output, file=sys.stderr, flush=True)

def log_info(message) -> None:
    """Helper method to print info."""
    print(f'-I- {message}', file=sys.stdout, flush=True)

def log_debug(message) -> None:
    """Helper method to print debug."""
    if DEBUG:
        print(f'-D- {message}', file=sys.stdout, flush=True)


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
        self.meta_data = None
        self.meta_img_tag = None
        self.meta_img_name = None
        self.meta_img_repo = None

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
        if self.image:
            if '/' in self.image:
                self.repository = '/'.join(self.image.split('/')[:-1])
                self.image = self.image.split('/')[-1]

        if not tarfile.is_tarfile(self.image_path):
            log_error(f'{self.image_path} is not a valid tar file')
        try:
            with tarfile.open(self.image_path, 'r') as t:
            # get the image manifest to determine image name and tag
                self.meta_data = json.load(t.extractfile(r'manifest.json'))
        except (json.JSONDecodeError, KeyError):
            pass
        if not self.meta_data:
            log_error(f"Could not extract manifest.json from {self.image_path}, verify that it is a valid Docker image")
        try:
            # take the first tag of the first image, there should be only one anyway
            self.meta_img_name = self.meta_data[0]['RepoTags'][0]
            if '/' in self.meta_img_name:
                self.meta_img_repo = '/'.join(self.meta_img_name.split('/')[:-1])
                self.meta_img_name = self.meta_img_name.split('/')[-1]
            self.meta_img_tag = self.meta_img_name.split(':')[1]
            self.meta_img_name = self.meta_img_name.split(':')[0]
            if not self.image:
                self.image = self.meta_img_name
            if not self.tag:
                self.tag = self.meta_img_tag
            # do not upload images without proper tag, to add latest add the latest flag
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
    
    def _check_image_locally(self,repo, image, tag) -> bool:
        """helper method to check if image already exists in local docker"""
        full_image_name = ""
        if repo:
            full_image_name += repo + "/"
        full_image_name += image
        log_debug(f'starting DockerHubUploader._check_image_locally with image:"{full_image_name}",tag:"{tag}"')
        for img in self.client.images.list():
            for img_name in  img.attrs['RepoTags']:
                if img_name == f"{full_image_name}:{tag}":
                    return True
        return False

    def _delete_image_locally(self,repo, image, tag) -> None:
        """Helper method to remove images from local docker"""
        full_image_name = ""
        if repo:
            full_image_name += repo + "/"
        full_image_name += image
        log_debug(f'starting DockerHubUploader._delete_image_locally with full_image_name={full_image_name} repo="{repo}", image:"{image}",tag:"{tag}"')
        try:
            self.client.images.remove(image=f'{full_image_name}:{tag}', force=True)
        except Exception as e:
            log_error(f"could not remove {full_image_name}:{tag}\n    {e}")

    def load_docker_img(self):
        """Load a docker file to docker engine"""
        log_debug(f'starting DockerHubUploader.load_docker_img with image:"{self.image}",tag:"{self.tag}", path:"{self.image_path}"')
        # check if meta_data name and tag are different from given image and tag
        new_tag_required = f'{self.meta_img_repo}/{self.meta_img_name}:{self.meta_img_tag}' != f'{self.repository}/{self.image}:{self.tag}'
        # Check if the image:tag already exists if so try to delete it.
        if self._check_image_locally(repo=self.repository, image=self.image, tag=self.tag):
            log_warning(f'{self.image}:{self.tag} was found locally removing it from docker engine.')
            try:
                self._delete_image_locally(repo=self.repository, image=self.image, tag=self.tag)
            except Exception as e:
                log_error(f'Could not delete {self.image}:{self.tag} from local docker.\n    {e}')
        if new_tag_required and self._check_image_locally(repo=self.meta_img_repo, image=self.meta_img_name, tag=self.meta_img_tag):
            log_warning(f'new_tag_required={new_tag_required} and {self.meta_img_repo}/{self.meta_img_name}:{self.meta_img_tag} was found locally removing it from docker engine.')
            try:
                self._delete_image_locally(repo=self.meta_img_repo, image=self.meta_img_name, tag=self.meta_img_tag)
            except Exception as e:
                log_error(f'Could not delete {self.meta_img_repo}/{self.meta_img_name}:{self.meta_img_tag} from local docker.\n    {e}')
        if not os.path.exists(self.image_path):
            log_error(f'{self.image_path} doesn\'t exists.')
        with open(self.image_path, 'rb') as img:
            try:
                _ = self.client.images.load(img)
                full_image_name = ""
                if self.meta_img_repo:
                    full_image_name += self.meta_img_repo +"/"
                full_image_name += self.meta_img_name
                log_info(f'Loaded {full_image_name}:{self.meta_img_tag} to local docker engine.')
                # re-tag the image if needed
                if new_tag_required:
                    self.tag_image(new_tag=self.tag, old_image=self.meta_img_name, old_repo=self.meta_img_repo, old_tag=self.meta_img_tag)
                    self.cleanup(repo=self.meta_img_repo, image=self.meta_img_name, tag=self.meta_img_tag)
            except Exception as e:
                log_error(f'Could not load the {self.repository}/{self.image}:{self.tag} to docker.\n    {e}')
                # tag as latest if latest flag exists

    def tag_image(self, new_tag, old_repo, old_image, old_tag):
        """Load a docker file to docker engine"""
        full_old_image_name = ""
        if old_repo:
            full_old_image_name += old_repo + "/"
        full_old_image_name += old_image
        log_debug(f'starting DockerHubUploader.tag_image with old_image:{full_old_image_name},new_image:"{self.repository}/{self.image}",current_tag:"{old_tag}", new_tag:"{new_tag}"')
         # check if new image name:tag exists locally
        if self._check_image_locally(repo=self.repository, image=self.image, tag=new_tag):
            log_warning(f'{self.repository}/{self.image}:{new_tag} was found locally removing it from docker engine.')
            try:
                self._delete_image_locally(repo=self.repository, image=self.image, tag=new_tag)
            except Exception as e:
                log_error(f'Could not delete {self.repository}/{self.image}:{new_tag} from local docker.\n    {e}')
        try:
            img = self.client.images.get(f'{full_old_image_name}:{old_tag}')
            img.tag(f'{self.repository}/{self.image}', new_tag)
            log_info(f'Tagged {full_old_image_name}:{self.tag} as {self.repository}/{self.image}:{new_tag}.')
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

    def cleanup(self,repo, image, tag):
        """Cleanup function to remove loaded docker images from host"""
        log_debug(f'starting DockerHubUploader.push_image with repo:"{repo}",image:"{image}"tag:"{tag}" ')
        if self._check_image_locally(repo=repo, image=image, tag=tag):
            self._delete_image_locally(repo=repo, image=image, tag=tag)

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
        dhu.tag_image(new_tag='latest',old_repo=dhu.repository,old_image=dhu.image,old_tag=dhu.tag)
        dhu.push_image('latest')
        dhu.cleanup(repo=dhu.repository,image=dhu.image,tag='latest')
    dhu.cleanup(repo=dhu.repository,image=dhu.image,tag=dhu.tag)
