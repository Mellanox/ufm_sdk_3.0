# UFM SDK 3.0



A new open-source SDK project for NVIDIA UFM ([Unified Fabric Manager](https://www.nvidia.com/en-us/networking/infiniband/ufm/))

![image](https://user-images.githubusercontent.com/3473601/166264210-740f11cd-e890-4e40-ad97-c95fafe32591.png)

## Main Features 

- scripts - list of python scripts as examples how to collect data and operate devices via UFM REST API
- plugins - list of evalable 3rd party plugins for UFM REST API. for example: Zabbix, Slurm, FluentD, etc..  
- utils   - tools for general usage over UFM REST API. some of them already in use in the available 3rd party plugins







## Documentation

[UFM REST API Documentation](https://docs.nvidia.com/networking/display/UFMEnterpriseRESTAPILatest)

[UFM User Manual](https://docs.nvidia.com/networking/display/UFMEnterpriseUMLatest)

[UFM Release Notes](https://docs.nvidia.com/networking/display/UFMEnterpriseUMLatest/Release+Notes)



## Installation

Install my-project with npm

```bash
  TBD
  
```

## Relase Job:
Please use the following in order to build:
http://hpc-master.lab.mtl.com:8080/job/UFM_PLUGINS_RELEASE/
    

# Adding Plugins to CI Pipeline

This project supports integration of custom plugins into the Continuous Integration (CI) pipeline. The process for integrating your plugin is simple and described below.

## Prerequisites

Your plugin should have a dedicated `.ci` directory that contains a `ci_matrix.yaml` file. This file is used by the CI pipeline to manage the build process for your plugin.

You can use the `ci_matrix.yaml` file found in the `hello_world_plugin` directory as a template.


## CI Configuration Steps

To add your plugin to the CI pipeline, follow these steps:

1. Create a `.ci` directory in your plugin's root directory.

2. In the `.ci` directory, create a `ci_matrix.yaml` file. Use the `ci_matrix.yaml` file in the `hello_world_plugin` directory as a template.

3. The CI pipeline will detect changes in your plugin directory and trigger the CI process. It uses the `ci_matrix.yaml` file in your plugin's `.ci` directory to manage the CI process.

## Important Note

If your plugin directory does not contain a `.ci` directory, the CI process will fail.

## CI Trigger

The CI pipeline gets triggered based on changes made to the plugins. If changes occur in multiple plugins, the pipeline will not trigger the individual `.ci` directories but instead trigger a default empty CI.

