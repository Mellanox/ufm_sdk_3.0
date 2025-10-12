#!/usr/bin/python3
"""
Docker Hub Multi-Architecture Uploader

This script handles uploading multi-architecture Docker images to Docker Hub.
It takes two architecture-specific images (ARM and AMD), uploads them to separate
repositories, and creates a multi-architecture manifest that references both.

Architecture:
- {image_name}_amd - AMD64 specific image
- {image_name}_arm - ARM64 specific image  
- {image_name} - Multi-arch manifest (references both)

Usage:
    python3 dockerhub_multiarch_uploader.py -u USER -p TOKEN \\
        --amd-path /path/to/amd.tar --arm-path /path/to/arm.tar \\
        -i image_name -t tag_version -r repository_name
"""

import requests
import sys
import os
import docker
import argparse
import json
import tarfile
import subprocess
from typing import Tuple, Optional


DEBUG = os.environ.get('DEBUG', None)


def log_error(message: str) -> None:
    """Helper method to print errors and exit."""
    if hasattr(sys.stderr, 'isatty') and sys.stderr.isatty():
        output = f'\033[0;31m-E- {message}\033[0m'
    else:
        output = f'-E- {message}'
    print(output, file=sys.stderr, flush=True)
    sys.exit(1)


def log_warning(message: str) -> None:
    if hasattr(sys.stderr, 'isatty') and sys.stderr.isatty():
        output = f'\033[1;33m-W- {message}\033[0m'
    else:
        output = f'-W- {message}'
    print(output, file=sys.stderr, flush=True)


def log_info(message: str) -> None:
    """Helper method to print info."""
    print(f'-I- {message}', file=sys.stdout, flush=True)


def log_debug(message: str) -> None:
    """Helper method to print debug."""
    if DEBUG:
        print(f'-D- {message}', file=sys.stdout, flush=True)


class DockerHubMultiArchUploader:
    """
    Helper class to upload multi-architecture images to Docker Hub.
    
    This class handles:
    1. Loading ARM and AMD Docker images
    2. Pushing them to separate arch-specific repositories
    3. Creating a multi-arch manifest that references both
    
    Args:
        username (str): Docker Hub username
        password (str): Docker Hub password/access-token
        repository (str): Docker Hub repository (default: 'mellanox')
    """
    DOCKERHUB_URL = r'https://hub.docker.com'
    DOCKERHUB_API_VER = '/v2'

    def __init__(self, username: str, password: str, repository: str = 'mellanox') -> None:
        self.username = username
        self.password = password
        self.session = requests.session()
        self.repository = repository
        self.token = None
        self.client = docker.from_env()
        
        # Image properties
        self.image_name = ""
        self.tag = ""
        self.amd_image_path = ""
        self.arm_image_path = ""
        
        # Metadata from image files
        self.amd_meta_data = None
        self.arm_meta_data = None

    def login(self) -> None:
        """Login to Docker Hub for validation and API access."""
        log_debug('Starting DockerHubMultiArchUploader.login')
        url = self.DOCKERHUB_URL + self.DOCKERHUB_API_VER + '/users/login'
        data = {
            "username": self.username,
            "password": self.password
        }
        response = self.session.post(url=url, data=data)
        if response.status_code == 200 and 'token' in response.json():
            self.token = response.json()['token']
            log_info('Acquired Docker Hub token successfully')
            log_debug(f'Token: "{self.token}"')
        else:
            log_error(f'Could not acquire token from Docker Hub. Please verify credentials.\n{response.text}')

    def validate_image_file(self, image_path: str, arch: str) -> dict:
        """
        Validate that the image file exists and is a valid Docker tar file.
        
        Args:
            image_path (str): Path to the Docker image tar file
            arch (str): Architecture label (for logging)
            
        Returns:
            dict: Metadata from manifest.json
        """
        log_debug(f'Validating {arch} image: {image_path}')
        
        if not os.path.exists(image_path):
            log_error(f'{arch} image path does not exist: {image_path}')
            
        if not tarfile.is_tarfile(image_path):
            log_error(f'{arch} image is not a valid tar file: {image_path}')
            
        try:
            with tarfile.open(image_path, 'r') as t:
                meta_data = json.load(t.extractfile('manifest.json'))
                log_info(f'Successfully validated {arch} image: {image_path}')
                return meta_data
        except (json.JSONDecodeError, KeyError) as e:
            log_error(f"Could not extract manifest.json from {arch} image {image_path}. Error: {e}")
        except Exception as e:
            log_error(f"Error reading {arch} image {image_path}: {e}")

    def check_image_tag_docker_hub(self, image_name: str, tag: str) -> bool:
        """
        Check if an image tag already exists on Docker Hub.
        
        Args:
            image_name (str): Name of the image
            tag (str): Tag to check
            
        Returns:
            bool: True if exists, False otherwise
        """
        log_debug(f'Checking if {self.repository}/{image_name}:{tag} exists on Docker Hub')
        url = self.DOCKERHUB_URL + self.DOCKERHUB_API_VER + f'/repositories/{self.repository}/{image_name}/tags'
        headers = {
            'Authorization': f'Bearer {self.token}'
        }
        
        while True:
            response = self.session.get(url=url, headers=headers)
            log_debug(f'Check image response status: {response.status_code}')
            
            if response.status_code == 200:
                image_tags = response.json()
                for result in image_tags['results']:
                    if result['name'] == tag:
                        log_info(f'Image {self.repository}/{image_name}:{tag} already exists on Docker Hub')
                        return True
                        
                # Check next page if available
                if image_tags.get('next'):
                    url = image_tags['next']
                else:
                    log_info(f'Image {self.repository}/{image_name}:{tag} not found on Docker Hub')
                    break
                    
            elif response.status_code == 404:
                log_warning(f"Repository {self.repository}/{image_name} not found on Docker Hub (will be created)")
                break
            else:
                log_error(f'Could not check Docker Hub. Status code: {response.status_code}\n{response.text}')
                
        return False

    def _check_image_locally(self, full_image_name: str, tag: str) -> bool:
        """Check if image exists in local Docker."""
        log_debug(f'Checking if {full_image_name}:{tag} exists locally')
        try:
            for img in self.client.images.list():
                if img.attrs.get('RepoTags'):
                    for img_tag in img.attrs['RepoTags']:
                        if img_tag == f"{full_image_name}:{tag}":
                            return True
        except Exception as e:
            log_warning(f'Error checking local images: {e}')
        return False

    def _delete_image_locally(self, full_image_name: str, tag: str) -> None:
        """Delete an image from local Docker."""
        log_debug(f'Deleting {full_image_name}:{tag} from local Docker')
        try:
            self.client.images.remove(image=f'{full_image_name}:{tag}', force=True)
            log_info(f'Removed {full_image_name}:{tag} from local Docker')
        except Exception as e:
            log_warning(f"Could not remove {full_image_name}:{tag}: {e}")

    def load_docker_image(self, image_path: str, target_name: str, target_tag: str) -> str:
        """
        Load a Docker image from tar file and tag it appropriately.
        
        Args:
            image_path (str): Path to the tar file
            target_name (str): Target image name (e.g., 'image_amd')
            target_tag (str): Target tag
            
        Returns:
            str: Full image name with repository
        """
        full_target_name = f'{self.repository}/{target_name}'
        log_info(f'Loading image to {full_target_name}:{target_tag}')
        
        # Clean up existing image if present
        if self._check_image_locally(full_target_name, target_tag):
            log_warning(f'{full_target_name}:{target_tag} found locally, removing it')
            self._delete_image_locally(full_target_name, target_tag)
        
        # Load the image
        try:
            with open(image_path, 'rb') as img_file:
                loaded_images = self.client.images.load(img_file.read())
                log_debug(f'Loaded images: {loaded_images}')
                
                if not loaded_images:
                    log_error(f'No images were loaded from {image_path}')
                
                # Get the loaded image (should be first/only one)
                loaded_image = loaded_images[0]
                original_tags = loaded_image.tags
                log_info(f'Loaded image with original tags: {original_tags}')
                
                # Tag with our target name
                loaded_image.tag(full_target_name, target_tag)
                log_info(f'Tagged image as {full_target_name}:{target_tag}')
                
                # Clean up original tags if different
                for orig_tag in original_tags:
                    if orig_tag != f'{full_target_name}:{target_tag}':
                        try:
                            self.client.images.remove(orig_tag, force=False)
                            log_debug(f'Removed original tag: {orig_tag}')
                        except:
                            pass  # Ignore errors on cleanup
                            
                return full_target_name
                
        except Exception as e:
            log_error(f'Could not load image from {image_path}: {e}')

    def push_image(self, image_name: str, tag: str) -> None:
        """
        Push an image to Docker Hub.
        
        Args:
            image_name (str): Full image name with repository
            tag (str): Tag to push
        """
        log_info(f'Pushing {image_name}:{tag} to Docker Hub')
        
        try:
            result = self.client.images.push(
                repository=image_name,
                tag=tag,
                auth_config={'username': self.username, 'password': self.password},
                stream=True,
                decode=True
            )
            
            for line in result:
                if 'error' in line:
                    log_error(f'Could not push {image_name}:{tag}\nError: {line["error"]}')
                if 'status' in line:
                    log_debug(f'Push status: {line["status"]}')
                    
            log_info(f'Successfully pushed {image_name}:{tag}')
            
        except Exception as e:
            log_error(f'Could not push {image_name}:{tag} to Docker Hub: {e}')

    def verify_arch_images_exist(self, amd_image: str, amd_tag: str, 
                                  arm_image: str, arm_tag: str) -> None:
        """
        Verify that both architecture-specific images exist on Docker Hub.
        
        This is a critical safety check before creating the multi-arch manifest.
        If either image is missing, the manifest creation will fail.
        
        Args:
            amd_image (str): AMD image name (e.g., 'image_amd')
            amd_tag (str): AMD image tag
            arm_image (str): ARM image name (e.g., 'image_arm')
            arm_tag (str): ARM image tag
        """
        log_info('Verifying both architecture images exist on Docker Hub before creating manifest')
        
        missing_images = []
        
        # Check AMD image
        if not self.check_image_tag_docker_hub(amd_image, amd_tag):
            missing_images.append(f'{self.repository}/{amd_image}:{amd_tag}')
        else:
            log_info(f'✓ Confirmed {self.repository}/{amd_image}:{amd_tag} exists on Docker Hub')
        
        # Check ARM image
        if not self.check_image_tag_docker_hub(arm_image, arm_tag):
            missing_images.append(f'{self.repository}/{arm_image}:{arm_tag}')
        else:
            log_info(f'✓ Confirmed {self.repository}/{arm_image}:{arm_tag} exists on Docker Hub')
        
        if missing_images:
            log_error(
                f'Cannot create multi-arch manifest. The following required images are missing from Docker Hub:\n' +
                '\n'.join(f'  - {img}' for img in missing_images) +
                '\n\nBoth architecture-specific images must be successfully pushed before creating the manifest.\n' +
                'Please check the push logs above for errors.'
            )

    def create_and_push_manifest(self, manifest_name: str, tag: str, 
                                  amd_image: str, arm_image: str) -> None:
        """
        Create and push a multi-arch manifest.
        
        Args:
            manifest_name (str): Name for the manifest (e.g., 'mellanox/image')
            tag (str): Tag for the manifest
            amd_image (str): Full AMD image reference (e.g., 'mellanox/image_amd:tag')
            arm_image (str): Full ARM image reference (e.g., 'mellanox/image_arm:tag')
        """
        log_info(f'Creating multi-arch manifest: {manifest_name}:{tag}')
        log_info(f'  AMD image: {amd_image}')
        log_info(f'  ARM image: {arm_image}')
        
        # First, create the manifest
        create_cmd = [
            'docker', 'manifest', 'create',
            f'{manifest_name}:{tag}',
            '--amend', amd_image,
            '--amend', arm_image
        ]
        
        log_debug(f'Running: {" ".join(create_cmd)}')
        
        try:
            result = subprocess.run(
                create_cmd,
                capture_output=True,
                text=True,
                check=True
            )
            log_info(f'Manifest created successfully')
            log_debug(f'Create output: {result.stdout}')
            
        except subprocess.CalledProcessError as e:
            log_error(f'Failed to create manifest:\nSTDOUT: {e.stdout}\nSTDERR: {e.stderr}')
        except Exception as e:
            log_error(f'Error creating manifest: {e}')
        
        # Now push the manifest
        push_cmd = [
            'docker', 'manifest', 'push',
            f'{manifest_name}:{tag}'
        ]
        
        log_debug(f'Running: {" ".join(push_cmd)}')
        
        try:
            result = subprocess.run(
                push_cmd,
                capture_output=True,
                text=True,
                check=True
            )
            log_info(f'Manifest pushed successfully: {manifest_name}:{tag}')
            log_debug(f'Push output: {result.stdout}')
            
        except subprocess.CalledProcessError as e:
            log_error(f'Failed to push manifest:\nSTDOUT: {e.stdout}\nSTDERR: {e.stderr}')
        except Exception as e:
            log_error(f'Error pushing manifest: {e}')

    def cleanup_local_images(self, images_to_clean: list) -> None:
        """
        Clean up local Docker images.
        
        Args:
            images_to_clean (list): List of (image_name, tag) tuples to remove
        """
        log_info('Cleaning up local Docker images')
        for image_name, tag in images_to_clean:
            if self._check_image_locally(image_name, tag):
                self._delete_image_locally(image_name, tag)

    def upload_multiarch(self, force: bool = False, add_latest: bool = False) -> None:
        """
        Main method to orchestrate multi-arch upload.
        
        Args:
            force (bool): Force overwrite if images exist
            add_latest (bool): Also tag as 'latest'
        """
        log_info('='*80)
        log_info('Starting Multi-Architecture Docker Hub Upload')
        log_info('='*80)
        
        # Validate both image files
        log_info('Step 1/7: Validating image files')
        self.amd_meta_data = self.validate_image_file(self.amd_image_path, 'AMD')
        self.arm_meta_data = self.validate_image_file(self.arm_image_path, 'ARM')
        
        # Define image names
        amd_image_name = f'{self.image_name}_amd'
        arm_image_name = f'{self.image_name}_arm'
        multiarch_image_name = self.image_name
        
        # Check if images already exist on Docker Hub
        log_info('Step 2/7: Checking Docker Hub for existing images')
        
        images_exist = []
        for img_name in [amd_image_name, arm_image_name, multiarch_image_name]:
            if self.check_image_tag_docker_hub(img_name, self.tag):
                images_exist.append(f'{self.repository}/{img_name}:{self.tag}')
        
        if images_exist and not force:
            log_error(
                f'The following images already exist on Docker Hub:\n' +
                '\n'.join(f'  - {img}' for img in images_exist) +
                '\n\nUse --force flag to overwrite.'
            )
        elif images_exist:
            log_warning(f'Force flag enabled. Will overwrite existing images:\n' +
                       '\n'.join(f'  - {img}' for img in images_exist))
        
        # Load and tag AMD image
        log_info('Step 3/7: Loading and tagging AMD image')
        amd_full_name = self.load_docker_image(self.amd_image_path, amd_image_name, self.tag)
        
        # Load and tag ARM image
        log_info('Step 4/7: Loading and tagging ARM image')
        arm_full_name = self.load_docker_image(self.arm_image_path, arm_image_name, self.tag)
        
        # Push AMD image
        log_info('Step 5/7: Pushing AMD image to Docker Hub')
        self.push_image(amd_full_name, self.tag)
        
        # Push ARM image
        log_info('Step 6/7: Pushing ARM image to Docker Hub')
        self.push_image(arm_full_name, self.tag)
        
        # Verify both images exist on Docker Hub before creating manifest
        log_info('Step 6.5/7: Verifying both architecture images are on Docker Hub')
        self.verify_arch_images_exist(amd_image_name, self.tag, arm_image_name, self.tag)
        
        # Create and push multi-arch manifest
        log_info('Step 7/7: Creating and pushing multi-arch manifest')
        multiarch_full_name = f'{self.repository}/{multiarch_image_name}'
        self.create_and_push_manifest(
            multiarch_full_name,
            self.tag,
            f'{amd_full_name}:{self.tag}',
            f'{arm_full_name}:{self.tag}'
        )
        
        # Handle 'latest' tag if requested
        if add_latest:
            log_info('='*80)
            log_info('Processing "latest" tag')
            log_info('='*80)
            
            # Check if latest already exists
            latest_exists = []
            for img_name in [amd_image_name, arm_image_name, multiarch_image_name]:
                if self.check_image_tag_docker_hub(img_name, 'latest'):
                    latest_exists.append(f'{self.repository}/{img_name}:latest')
            
            if latest_exists and not force:
                log_warning(
                    f'Latest tags already exist for:\n' +
                    '\n'.join(f'  - {img}' for img in latest_exists) +
                    '\nSkipping latest tag creation.'
                )
            else:
                # Tag images as latest
                log_info('Tagging AMD image as latest')
                amd_img = self.client.images.get(f'{amd_full_name}:{self.tag}')
                amd_img.tag(amd_full_name, 'latest')
                
                log_info('Tagging ARM image as latest')
                arm_img = self.client.images.get(f'{arm_full_name}:{self.tag}')
                arm_img.tag(arm_full_name, 'latest')
                
                # Push latest tags
                log_info('Pushing AMD latest to Docker Hub')
                self.push_image(amd_full_name, 'latest')
                
                log_info('Pushing ARM latest to Docker Hub')
                self.push_image(arm_full_name, 'latest')
                
                # Verify both latest images exist on Docker Hub before creating manifest
                log_info('Verifying both architecture "latest" images are on Docker Hub')
                self.verify_arch_images_exist(amd_image_name, 'latest', arm_image_name, 'latest')
                
                # Create manifest for latest
                log_info('Creating and pushing multi-arch manifest for latest')
                self.create_and_push_manifest(
                    multiarch_full_name,
                    'latest',
                    f'{amd_full_name}:latest',
                    f'{arm_full_name}:latest'
                )
                
                # Add latest tags to cleanup
                images_to_cleanup = [
                    (amd_full_name, 'latest'),
                    (arm_full_name, 'latest')
                ]
                self.cleanup_local_images(images_to_cleanup)
        
        # Cleanup local images
        log_info('='*80)
        log_info('Cleaning up local Docker images')
        log_info('='*80)
        images_to_cleanup = [
            (amd_full_name, self.tag),
            (arm_full_name, self.tag)
        ]
        self.cleanup_local_images(images_to_cleanup)
        
        log_info('='*80)
        log_info('Multi-Architecture Upload Complete!')
        log_info('='*80)
        log_info(f'AMD Image: {amd_full_name}:{self.tag}')
        log_info(f'ARM Image: {arm_full_name}:{self.tag}')
        log_info(f'Multi-Arch: {multiarch_full_name}:{self.tag}')
        if add_latest:
            log_info(f'Latest: {multiarch_full_name}:latest')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        prog='dockerhub_multiarch_uploader',
        description='Upload multi-architecture Docker images to Docker Hub',
        epilog='Example: python3 %(prog)s -u user -p token --amd-path amd.tar --arm-path arm.tar -i myimage -t v1.0'
    )
    
    # Required arguments
    parser.add_argument('-u', '--username', type=str, 
                       help='Docker Hub username (or set DOCKERHUB_USER env var)')
    parser.add_argument('-p', '--password', type=str, 
                       help='Docker Hub password/token (or set DOCKERHUB_PASS env var)')
    parser.add_argument('--amd-path', type=str, required=True,
                       help='Path to AMD64 Docker image tar file')
    parser.add_argument('--arm-path', type=str, required=True,
                       help='Path to ARM64 Docker image tar file')
    parser.add_argument('-i', '--image', type=str, required=True,
                       help='Base image name (without arch suffix)')
    parser.add_argument('-t', '--tag', type=str, required=True,
                       help='Image tag (version)')
    parser.add_argument('-r', '--repository', type=str, required=True, 
                        default='mellanox', help='Docker Hub repository (default: mellanox)')
    
    # Optional arguments
    parser.add_argument('-f', '--force', default=False, action='store_true',
                       help='Force push even if images exist (use with caution)')
    parser.add_argument('-l', '--latest', default=False, action='store_true',
                       help='Also tag as "latest"')
    
    args = parser.parse_args()
    
    # Get credentials from args or environment
    username = args.username or os.environ.get('DOCKERHUB_USER')
    password = args.password or os.environ.get('DOCKERHUB_PASS')
    
    if not username:
        log_error(
            "Docker Hub username must be specified using -u/--username or by setting\n"
            "    DOCKERHUB_USER=<username> environment variable"
        )
    
    if not password:
        log_error(
            "Docker Hub password must be specified using -p/--password or by setting\n"
            "    DOCKERHUB_PASS=<password/token> environment variable"
        )
    
    # Validate tag
    if args.tag == 'latest':
        log_error(
            'Invalid tag "latest". Please use a specific version number.\n'
            '    Use the --latest flag to also tag as latest.'
        )
    
    # Warnings
    if args.force:
        log_warning('Force push enabled - existing images will be overwritten')
    
    if args.latest:
        log_warning('"latest" tag will be created in addition to version tag')
    
    # Create uploader and run
    try:
        uploader = DockerHubMultiArchUploader(username, password, args.repository)
        uploader.image_name = args.image
        uploader.tag = args.tag
        uploader.amd_image_path = args.amd_path
        uploader.arm_image_path = args.arm_path
        
        uploader.login()
        uploader.upload_multiarch(force=args.force, add_latest=args.latest)
        
        log_info('SUCCESS: All operations completed successfully!')
        sys.exit(0)
        
    except KeyboardInterrupt:
        log_error('Operation cancelled by user')
    except Exception as e:
        log_error(f'Unexpected error: {e}')

