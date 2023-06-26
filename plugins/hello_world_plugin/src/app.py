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

app = Flask(__name__)


@app.route('/hello')
def helloIndex():
    return 'Hello World!'


if __name__ == '__main__':
   app.run(host='127.0.0.1', port=8687)
