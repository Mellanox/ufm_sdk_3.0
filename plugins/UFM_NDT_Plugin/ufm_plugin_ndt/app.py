from flask import Flask, request, make_response
from flask_restful import Resource, Api
from requests.auth import HTTPBasicAuth
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime

import gzip
import requests
import logging

app = Flask(__name__)
app.config.from_pyfile('plugin.cfg')
logging.basicConfig(filename=app.config['LOGS_FILENAME'],
                    level=app.config['LOGS_LEVEL'],
                    format='%(asctime)s %(levelname)s %(name)s %(threadName)s : %(message)s')
api = Api(app)

PORTS_JOB = None
PORTS_JSON = None
PORTS_AS_TEXT = None
PORTS_AS_TEXT_PREPARED_AHEAD = None
PORTS_AS_TEXT_COMPRESSED = None
#####
LINKS_JOB = None
LINKS_JSON = None
LINKS_AS_TEXT = None
LINKS_AS_TEXT_PREPARED_AHEAD = None
LINKS_AS_TEXT_COMPRESSED = None
#####
DEFAULT_SESSION_JOB = None
DEFAULT_SESSION_JSON = None
DEFAULT_SESSION_AS_TEXT = None
DEFAULT_SESSION_AS_TEXT_PREPARED_AHEAD = None
DEFAULT_SESSION_AS_TEXT_COMPRESSED = None
#####
VERSIONING_JOB = None
VERSIONING_JSON = None
VERSIONING_AS_TEXT = None
VERSIONING_AS_TEXT_PREPARED_AHEAD = None
VERSIONING_AS_TEXT_COMPRESSED = None


def send_ufm_request(url):
    ip = app.config['IP']
    username = app.config['USERNAME']
    password = app.config['PASSWORD']
    ws_protocol = app.config['WS_PROTOCOL']
    url = ws_protocol+'://'+ip+'/ufmRest/'+url
    try:
        response = requests.get(url, verify=False, auth=HTTPBasicAuth(username, password))
        app.logger.info("UFM API Request "+url)
        app.logger.info("UFM API Response "+url+" "+str(response.status_code))
        if response.raise_for_status():
            app.logger.error(response.raise_for_status())
    except Exception as e:
        app.logger.error(e)
    return response


def get_ufm_ports():
    global PORTS_JOB
    global PORTS_JSON
    global PORTS_AS_TEXT
    global PORTS_AS_TEXT_PREPARED_AHEAD
    global PORTS_AS_TEXT_COMPRESSED
    if PORTS_JOB:
        PORTS_JOB.pause()
    url = 'resources/ports'
    res = send_ufm_request(url)
    PORTS_JSON = res.json()
    PORTS_AS_TEXT = res.text
    with app.app_context():
        PORTS_AS_TEXT_PREPARED_AHEAD = make_response(PORTS_AS_TEXT)
        PORTS_AS_TEXT_PREPARED_AHEAD.headers['Content-length'] = len(PORTS_AS_TEXT)
    PORTS_AS_TEXT_COMPRESSED = gzip.compress(PORTS_AS_TEXT.encode('utf8'), 5)
    if PORTS_JOB:
        PORTS_JOB.resume()
    return PORTS_JSON


def get_ufm_links():
    global LINKS_JOB
    global LINKS_JSON
    global LINKS_AS_TEXT
    global LINKS_AS_TEXT_PREPARED_AHEAD
    global LINKS_AS_TEXT_COMPRESSED
    if LINKS_JOB:
        LINKS_JOB.pause()
    url = 'resources/links'
    res = send_ufm_request(url)
    LINKS_JSON = res.json()
    LINKS_AS_TEXT = res.text
    with app.app_context():
        LINKS_AS_TEXT_PREPARED_AHEAD = make_response(LINKS_AS_TEXT)
        LINKS_AS_TEXT_PREPARED_AHEAD.headers['Content-length'] = len(LINKS_AS_TEXT)
    LINKS_AS_TEXT_COMPRESSED = gzip.compress(LINKS_AS_TEXT.encode('utf8'), 5)
    if LINKS_JOB:
        LINKS_JOB.resume()
    return LINKS_JSON


def get_ufm_default_session():
    global DEFAULT_SESSION_JOB
    global DEFAULT_SESSION_JSON
    global DEFAULT_SESSION_AS_TEXT
    global DEFAULT_SESSION_AS_TEXT_PREPARED_AHEAD
    global DEFAULT_SESSION_AS_TEXT_COMPRESSED
    if DEFAULT_SESSION_JOB:
        DEFAULT_SESSION_JOB.pause()
    url = 'monitoring/session/0/data'
    res = send_ufm_request(url)
    DEFAULT_SESSION_JSON = res.json()
    DEFAULT_SESSION_AS_TEXT = res.text
    with app.app_context():
        DEFAULT_SESSION_AS_TEXT_PREPARED_AHEAD = make_response(DEFAULT_SESSION_AS_TEXT)
        DEFAULT_SESSION_AS_TEXT_PREPARED_AHEAD.headers['Content-length'] = len(DEFAULT_SESSION_AS_TEXT)
    DEFAULT_SESSION_AS_TEXT_COMPRESSED = gzip.compress(DEFAULT_SESSION_AS_TEXT.encode('utf8'), 5)
    if DEFAULT_SESSION_JOB:
        DEFAULT_SESSION_JOB.resume()
    return DEFAULT_SESSION_JSON


def get_ufm_versioning():
    global VERSIONING_JOB
    global VERSIONING_JSON
    global VERSIONING_AS_TEXT
    global VERSIONING_AS_TEXT_PREPARED_AHEAD
    global VERSIONING_AS_TEXT_COMPRESSED
    if VERSIONING_JOB:
        VERSIONING_JOB.pause()
    url = 'app/versioning'
    res = send_ufm_request(url)
    VERSIONING_JSON = res.json()
    VERSIONING_AS_TEXT = res.text
    with app.app_context():
        VERSIONING_AS_TEXT_PREPARED_AHEAD = make_response(VERSIONING_AS_TEXT)
        VERSIONING_AS_TEXT_PREPARED_AHEAD.headers['Content-length'] = len(VERSIONING_AS_TEXT)
    VERSIONING_AS_TEXT_COMPRESSED = gzip.compress(VERSIONING_AS_TEXT.encode('utf8'), 5)
    if VERSIONING_JOB:
        VERSIONING_JOB.resume()
    return VERSIONING_JSON


class GetUFMPorts(Resource):
    def get(self):
        return get_ufm_ports()


class GetCachedUFMPortsAsTextPreparedAhead(Resource):
    def get(self):
        return PORTS_AS_TEXT_PREPARED_AHEAD


class GetCachedUFMPortsAsCompressedWithValidHeaderType(Resource):
    def get(self):
        ports_response_compressed = make_response(PORTS_AS_TEXT_COMPRESSED)
        ports_response_compressed.headers['Content-length'] = len(PORTS_AS_TEXT_COMPRESSED)
        ports_response_compressed.headers['Content-Type'] = 'gzip'
        ports_response_compressed.headers['Content-Encoding'] = 'gzip'
        return ports_response_compressed


class GetUFMLinks(Resource):
    def get(self):
        return get_ufm_links()


class GetCachedUFMLinksAsTextPreparedAhead(Resource):
    def get(self):
        return LINKS_AS_TEXT_PREPARED_AHEAD


class GetCachedUFMLinksAsCompressedWithValidHeaderType(Resource):
    def get(self):
        links_response_compressed = make_response(LINKS_AS_TEXT_COMPRESSED)
        links_response_compressed.headers['Content-length'] = len(LINKS_AS_TEXT_COMPRESSED)
        links_response_compressed.headers['Content-Type'] = 'gzip'
        links_response_compressed.headers['Content-Encoding'] = 'gzip'
        return links_response_compressed


class GetUFMVersioning(Resource):
    def get(self):
        return get_ufm_versioning()


class GetCachedUFMVersioningAsTextPreparedAhead(Resource):
    def get(self):
        return VERSIONING_AS_TEXT_PREPARED_AHEAD


class GetCachedUFMVersioningAsCompressedWithValidHeaderType(Resource):
    def get(self):
        versioning_response_compressed = make_response(VERSIONING_AS_TEXT_COMPRESSED)
        versioning_response_compressed.headers['Content-length'] = len(VERSIONING_AS_TEXT_COMPRESSED)
        versioning_response_compressed.headers['Content-Type'] = 'gzip'
        versioning_response_compressed.headers['Content-Encoding'] = 'gzip'
        return versioning_response_compressed


class GetUFMDefaultSession(Resource):
    def get(self):
        return get_ufm_default_session()


class GetCachedUFMDefaultSessionAsTextPreparedAhead(Resource):
    def get(self):
        return DEFAULT_SESSION_AS_TEXT_PREPARED_AHEAD


class GetCachedUFMDefaultSessionAsCompressedWithValidHeaderType(Resource):
    def get(self):
        default_session_response_compressed = make_response(DEFAULT_SESSION_AS_TEXT_COMPRESSED)
        default_session_response_compressed.headers['Content-length'] = len(DEFAULT_SESSION_AS_TEXT_COMPRESSED)
        default_session_response_compressed.headers['Content-Type'] = 'gzip'
        default_session_response_compressed.headers['Content-Encoding'] = 'gzip'
        return default_session_response_compressed


api.add_resource(GetUFMPorts, '/ufm_ports')
api.add_resource(GetCachedUFMPortsAsTextPreparedAhead, '/ufm_cached_ports_as_text_prepared_ahead')
api.add_resource(GetCachedUFMPortsAsCompressedWithValidHeaderType, '/ufm_cached_ports_as_text_compressed_wth_valid_header_type')
api.add_resource(GetUFMLinks, '/ufm_links')
api.add_resource(GetCachedUFMLinksAsTextPreparedAhead, '/ufm_cached_links_as_text_prepared_ahead')
api.add_resource(GetCachedUFMLinksAsCompressedWithValidHeaderType, '/ufm_cached_links_as_text_compressed_wth_valid_header_type')
api.add_resource(GetUFMVersioning, '/ufm_versioning')
api.add_resource(GetCachedUFMVersioningAsTextPreparedAhead, '/ufm_cached_versioning_as_text_prepared_ahead')
api.add_resource(GetCachedUFMVersioningAsCompressedWithValidHeaderType, '/ufm_cached_versioning_as_text_compressed_wth_valid_header_type')
api.add_resource(GetUFMDefaultSession, '/ufm_default_session')
api.add_resource(GetCachedUFMDefaultSessionAsTextPreparedAhead, '/ufm_cached_default_session_as_text_prepared_ahead')
api.add_resource(GetCachedUFMDefaultSessionAsCompressedWithValidHeaderType, '/ufm_cached_default_session_as_text_compressed_wth_valid_header_type')


scheduler = BackgroundScheduler()
resources_polling_interval = app.config['RESOURCES_POLLING_INTERVAL']
default_session_polling_interval = app.config['DEFAULT_MONITORING_SESSION_POLLING_INTERVAL']
PORTS_JOB = scheduler.add_job(get_ufm_ports,'interval',seconds=resources_polling_interval, next_run_time=datetime.now())
LINKS_JOB = scheduler.add_job(get_ufm_links,'interval',seconds=resources_polling_interval, next_run_time=datetime.now())
VERSIONING_JOB = scheduler.add_job(get_ufm_versioning,'interval',seconds=resources_polling_interval, next_run_time=datetime.now())
DEFAULT_SESSION_JOB = scheduler.add_job(get_ufm_default_session,'interval',minutes=default_session_polling_interval, next_run_time=datetime.now())
try:
    scheduler.start()
    app.logger.info("Periodic UFM data polling started")
except Exception as e:
    app.logger.error("Periodic UFM data polling failed to start")
    app.logger.error(e)


@app.route('/')
def root():
    return app.send_static_file('index.html')


if __name__ == '__main__':
    app.run(debug=True)
