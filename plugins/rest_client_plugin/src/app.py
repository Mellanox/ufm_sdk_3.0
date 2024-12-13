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
# @date:   Feb 13, 2023
# Plugin App Template

from flask import Flask
import requests

app = Flask(__name__)

@app.route('/config')
def get_config():
    target_url = f"https://127.0.0.1/ufmRestV2/app/ufm_config"
    response = requests.get(target_url, verify=False, auth=('admin','123456'))
    return response.json()

@app.route('/events')
def get_events():
    target_url = f"https://127.0.0.1/ufmRestV2/app/events"
    response = requests.get(target_url, verify=False, auth=('admin','123456'))
    return response.json()

@app.route('/systems')
def get_systems():
    target_url = f"https://127.0.0.1/ufmRestV2/resources/systems"
    response = requests.get(target_url, verify=False, auth=('admin','123456'))
    return response.json()

if __name__ == '__main__':
   app.run(host='127.0.0.1', port=8688)
