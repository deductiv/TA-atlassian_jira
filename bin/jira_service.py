from future import standard_library
standard_library.install_aliases()
from builtins import object
import sys
import base64
import urllib.request, urllib.error, urllib.parse
import urllib.request, urllib.parse, urllib.error
from contextlib import closing
import json

import common
from common import logger

class JiraService(object):
    def __init__(self, username, password, host, port=443, protocol="https"):
        self.username = username
        self.password = password
        self.protocol = protocol
        self.port = port
        self.host = host

        self.auth = (username + ':' + password).encode('utf-8')
        self.encoded_auth = base64.b64encode(self.auth)

        self.jiraserver = protocol + '://' + host + ':' + port
        logger.info("jira server:%s" % self.jiraserver)

    def make_url_request_obj(self, url):
        logger.info("req %s" % url)
        req = urllib.request.Request(url)
        req.add_header('Content-Type', 'application/json; charset=utf-8')
        req.add_header('Authorization', 'Basic ' + self.encoded_auth.decode('utf-8'))
        return req

    def request(self, path):
        path = self.jiraserver + path
        req = self.make_url_request_obj(path)
        print('Connecting to URL: ' + path, file=sys.stderr)
        with closing(urllib.request.urlopen(req)) as raw_data:
            data = json.load(raw_data)
            print('Data: ' + str(data), file=sys.stderr)

        return data
