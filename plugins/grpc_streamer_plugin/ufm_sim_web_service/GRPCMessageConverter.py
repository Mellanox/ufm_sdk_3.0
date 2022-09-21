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
#
import json
from google.protobuf.any_pb2 import Any
from google.protobuf.json_format import MessageToJson
import plugins.grpc_streamer_plugin.ufm_sim_web_service.grpc_plugin_streamer_pb2 as grpc_plugin_streamer_pb2


def encode_message(params_dict):
    """
    get a dict with all data, and return a list of messages containing each of the params
    :param params_dict: dictoary with paramters from a rest api call respond
    :return: list of any message for a rpc send
    """
    output_list = []
    for key, value in params_dict.items():
        param = grpc_plugin_streamer_pb2.gRPCStreamerParams.Data(key=str(key), value=str(value))
        any_message = Any()
        any_message.Pack(param)
        output_list.append(any_message)
    return output_list


def decode_message(params_list):
    """
    get a list of any params and return a dict for rest api calls
    :param params_list: list of params in message form
    :return: dict of all the messages' data.
    """
    output_dict = {}
    for param_message in params_list:
        param_item_result = json.loads(MessageToJson(param_message))['value']
        output_dict[param_item_result['key']] = param_item_result['value']
    return output_dict


def encode_destination(job):
    """
    encode a destination to grpc DestinationParams
    :param job: Destination that we want to encode
    :return: DestinationParams
    """
    if not job:
        print("COULDNT FIND THE IP:"+job.dest_ip)
        return grpc_plugin_streamer_pb2.DestinationParams()

    params = []
    for item in job.calls:
        params.append(grpc_plugin_streamer_pb2.DestinationParams.APIParams(name=item[0],
                                                                             interval=item[1], only_delta=item[2]))

    return grpc_plugin_streamer_pb2.DestinationParams(ip=job.dest_ip, apiParams=params)


def decode_destination(request):
    """
    decode DestinationParams to Destination
    :param request:
    :return:
    """
    ip = request.ip
    param_results = []
    for x in request.apiParams:
        param_results.append((x.name, x.interval, x.only_delta))
    return ip, param_results
