#
# Copyright © 2013-2022 NVIDIA CORPORATION & AFFILIATES. ALL RIGHTS RESERVED.
#
# This software product is a proprietary product of Nvidia Corporation and its affiliates
# (the "Company") and all right, title, and interest in and to the software
# product, including all associated intellectual property rights, are and
# shall remain exclusively with the Company.
#
# This software product is governed by the End User License Agreement
# provided with the software product.
# @author: Anan Al-Aghbar
# @date:   Dec 20, 2022
#
from resources.base_resource import BaseResource


class BrightJobResource(BaseResource):
    BaseResource.ATTRS.update({
            "account": "account",
            "arguments": "arguments",
            "arrayID": "arrayID",
            "baseType": "baseType",
            "cgroup": "cgroup",
            "childType": "childType",
            "commandLineInterpreter": "commandLineInterpreter",
            "comment": "comment",
            "debug": "debug",
            "dependencies": "dependencies",
            "endtime": "endtime",
            "environmentVariables": "environmentVariables",
            "executable": "executable",
            "exitCode": "exitCode",
            "inqueue": "inqueue",
            "jobID": "jobID",
            "jobname": "jobname",
            "mailList": "mailList",
            "mailNotify": "mailNotify",
            "mailOptions": "mailOptions",
            "maxWallClock": "maxWallClock",
            "memoryUse": "memoryUse",
            "minMemPerNode": "minMemPerNode",
            "modified": "modified",
            "modules": "modules",
            "nodes": "nodes",
            "numberOfNodes": "numberOfNodes",
            "numberOfProcesses": "numberOfProcesses",
            "oldLocalUniqueKey": "oldLocalUniqueKey",
            "parallelEnvironment": "parallelEnvironment",
            "parentID": "parentID",
            "pendingReasons": "pendingReasons",
            "placement": "placement",
            "priority": "priority",
            "project": "project",
            "refJobQueueUniqueKey": "refJobQueueUniqueKey",
            "refWlmClusterUniqueKey": "refWlmClusterUniqueKey",
            "requestedCPUCores": "requestedCPUCores",
            "requestedCPUs": "requestedCPUs",
            "requestedGPUs": "requestedGPUs",
            "requestedMemory": "requestedMemory",
            "requestedSlots": "requestedSlots",
            "resourceList": "resourceList",
            "revision": "revision",
            "runWallClock": "runWallClock",
            "rundirectory": "rundirectory",
            "scriptFile": "scriptFile",
            "starttime": "starttime",
            "status": "status",
            "stderrfile": "stderrfile",
            "stdinfile": "stdinfile",
            "stdoutfile": "stdoutfile",
            "submittime": "submittime",
            "taskID": "taskID",
            "toBeRemoved": "toBeRemoved",
            "uniqueKey": "uniqueKey",
            "userdefined": "userdefined",
            "usergroup": "usergroup",
            "username": "username"
        })
    def __init__(self, obj):
        super(BrightJobResource, self).__init__(obj)