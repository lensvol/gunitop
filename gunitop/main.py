#coding: utf-8

import collections
import json
import socket
import sys
import threading
import time

workers = {}
# In seconds
PERIOD = 1


class ListenerThread(threading.Thread):

    def __init__(self, workers, host="localhost", port=18114):
        self.workers = workers
        self.stop = False
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        host = socket.gethostbyname(host)
        self.socket.bind((host, port))
        threading.Thread.__init__(self)

    def process(self, text):
        info = json.loads(text)
        info_type = info['type']
        pid = info['worker']['pid']
        worker = self.workers.setdefault(pid, {
            'ppid': -1,
            'status': u'Waiting...',
            'statistics': collections.Counter()
        })

        if info_type == 'spawn':
            worker['ppid'] = info['worker']['ppid']
            worker['status'] = u'Freshly spawned!'
        elif info_type == 'request':
            worker['status'] = '{0} {1}'.format(info['method'], info['path'])
        elif info_type == 'response':
            worker['status'] = 'Waiting...'
            worker['statistics'][info['status_code']] += 1

    def run(self):
        while not self.stop:
            text, source = self.socket.recvfrom(65535)
            self.process(text)

def main():
    listener = ListenerThread(workers)
    listener.start()

    try:
        while True:
            time.sleep(PERIOD)
            for pid, w in workers.items():
                print '{0} {1}'.format(pid, w['status'])
            print ''
            sys.stdout.flush()
    except (KeyboardInterrupt, SystemExit):
        listener.stop = True
        listener.join()
