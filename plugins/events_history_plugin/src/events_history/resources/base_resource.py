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
# @author: Abeer Moghrabi
# @date:   Aug 13, 2023
#


class BaseResource:
    ATTRS = {}

    def __init__(self, obj):
        if obj:
            self.model_to_obj(obj)

    def model_to_obj(self, obj):
        obj_dict = obj.__dict__
        for resource_attr, model_attr in self.ATTRS.items():
            value = obj_dict.get(model_attr)
            setattr(self, resource_attr, value)

