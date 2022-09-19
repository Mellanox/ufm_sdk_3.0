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
# @date:   Sep 19, 2022
#

from twisted.web import server
from twisted.web.wsgi import WSGIResource
from twisted.internet import reactor


def run_api(app, port_number):
    resource = WSGIResource(reactor, reactor.getThreadPool(), app)
    reactor.listenTCP(port_number, server.Site(resource,logPath=None))
    reactor.run()