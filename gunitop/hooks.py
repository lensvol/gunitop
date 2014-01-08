#coding: utf-8

import os
import socket
import time
import json


class Gunitop(object):
    def __init__(self, host="localhost", port=18114):
        self.comm_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.comm_socket.setblocking(False)
        self.address = (host, port)

    def _extract_worker_info(self, worker):
        return {
            'worker': {
                'pid': os.getpid(),
                'ppid': worker.ppid
            }
        }

    def _send(self, info):
        info['timestamp'] = int(time.time())
        text = json.dumps(info)
        self.comm_socket.sendto(text, self.address)

    def report_req(self, worker, req):
        info = self._extract_worker_info(worker)
        info.update({
            'method': req.method,
            'path': req.path,
            'type': 'request'
        })
        self._send(info)

    def report_resp(self, worker, req, env, resp):
        info = self._extract_worker_info(worker)
        info.update({
            'resp_length': resp.sent,
            'status_code': resp.status_code,
            'type': 'response',
            'method': req.method,
            'path': req.path
        })
        self._send(info)

    def get_pre_request(self):
        return (lambda w, r: self.report_req(w, r))

    def get_post_request(self):
        return (lambda w, r, e, resp: self.report_resp(w, r, e, resp))
