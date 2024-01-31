#
# Copyright © 2013-2024 NVIDIA CORPORATION & AFFILIATES. ALL RIGHTS RESERVED.
#
# This software product is a proprietary product of Nvidia Corporation and its affiliates
# (the "Company") and all right, title, and interest in and to the software
# product, including all associated intellectual property rights, are and
# shall remain exclusively with the Company.
#
# This software product is governed by the End User License Agreement
# provided with the software product.
#
# @author: Alexander Tolikin
# @date: 30 January, 2024
#

import helpers
from resources import Switch, UFMResource

if __name__ == "__main__":
    cli = Switch.get_cli(helpers.LOCAL_IP, "unregister")
    description = f"Unregister all the switches upon the plugin removal"
    registered_switches = UFMResource.read_json_file(helpers.ConfigParser.switches_file)
    status_code, headers = helpers.post_provisioning_api(cli, description, registered_switches)