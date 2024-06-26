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
import grpc_plugin_streamer_pb2 as grpc_plugin_streamer_pb2


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


def encode_subscriber(job):
    """
    encode a destination to grpc DestinationParams
    :param job: Destination that we want to encode
    :return: DestinationParams
    """
    if not job:
        print("COULDNT FIND THE IP:"+job.dest_ip)
        return grpc_plugin_streamer_pb2.SubscriberParams()

    params = []
    for item in job.calls:
        params.append(grpc_plugin_streamer_pb2.SubscriberParams.APIParams(ufm_api_name=item[0],
                                                                             interval=item[1], only_delta=item[2]))

    return grpc_plugin_streamer_pb2.SubscriberParams(job_id=job.dest_ip, apiParams=params)


def decode_subscriber(request):
    """
    decode DestinationParams to Destination
    :param request:
    :return:
    """
    ip = request.job_id
    param_results = []
    for x in request.apiParams:
        param_results.append((x.ufm_api_name, x.interval, x.only_delta))
    return ip, param_results
