#coding: utf-8

import os
import socket
import sys
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

    def report_spawn(self, server, worker):
        info = self._extract_worker_info(worker)
        info.update({
            'type': 'spawn'
        })
        self._send(info)

    def report_req(self, worker, req):
        info = self._extract_worker_info(worker)
        info.update({
            'method': req.method,
            'path': req.path,
            'type': 'request'
        })
        self._send(info)

    def report_exit(self, server, worker):
        info = self._extract_worker_info(worker)
        info['type'] = 'exit'
        self._send(info)

    def report_resp(self, worker, req, env, resp):
        # Checking if we were interrupted by SIGINT/SIGQUIT
        if not worker.alive:
            return

        info = self._extract_worker_info(worker)
        info.update({
            'resp_length': resp.sent,
            'status_code': resp.status_code,
            'type': 'response',
            'method': req.method,
            'path': req.path
        })
        self._send(info)

    def report_reload(self, server):
        info = {
            'type': 'reload',
            'ppid': server.pid,
        }
        self._send(info)

def setup_gunitop_hooks():
    g = Gunitop()

    handlers = {
        'post_fork': (lambda a, w: g.report_spawn(a, w)),
        'pre_request': (lambda w, r: g.report_req(w, r)),
        'post_request': (lambda w, r, e, resp: g.report_resp(w, r, e, resp)),
        'worker_exit': (lambda s, w: g.report_exit(s, w)),
        'on_reload': (lambda s: g.report_reload(s))
    }
    cfg_frame = sys._getframe(1)
    cfg_frame.f_globals.update(handlers)
