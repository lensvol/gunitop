#coding: utf-8

import curses
import collections
import json
import psutil
import math
import socket
import sys
import threading
import time

# for keeping track of y line offsets
from itertools import count

from ui import TabularWindow, animation, TestTabWindow

workers = {}
# In seconds
PERIOD = 1


class TabularMonitorWindow(TabularWindow):
    columns = [
        ('PID', 5),
        ('STATUS', 6),
        ('CPU', 4),
        ('VIRT', 6),
        ('RSS', 6),
        ('INFO', -1)
    ]

    def mem_as_text(self, amount):
        if amount > 1024 ** 2:
            return '{0}MB'.format(int(amount / 1024 ** 2))
        else:
            return '{0}B'.format(amount)

    def __init__(self, workers):
        self.workers = workers
        super(TabularMonitorWindow, self).__init__()

    def get_rows(self):
        result = []

        for pid, worker in self.workers.items():
            proc = worker['process']
            if not proc:
                continue

            try:
                (rss, vmem) = proc.get_memory_info()
                cpu = proc.get_cpu_percent()
            except psutil._error.NoSuchProcess:
                continue

            result.append((pid,
                           worker['status'],
                           '%i%%' % math.ceil(cpu),
                           self.mem_as_text(rss),
                           self.mem_as_text(vmem),
                           worker.get('text', '')))
        return result

class ListenerThread(threading.Thread):

    def __init__(self, workers, host="localhost", port=18114):
        self.workers = workers
        self.stop = False
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        host = socket.gethostbyname(host)
        self.socket.bind((host, port))
        self.socket.setblocking(False)
        threading.Thread.__init__(self)

    def process(self, text):
        info = json.loads(text)
        info_type = info['type']

        if info_type == 'reload':
            # Server event
            pid = info['ppid']
            for worker in workers.values():
                if worker['ppid'] == pid:
                    worker['status'] = 'EXIT'
                    worker['text'] = 'SIGHUP reload'
            return

        pid = info['worker']['pid']
        worker = self.workers.setdefault(pid, {
            'ppid': -1,
            'text': u'Waiting...',
            'status': 'IDLE',
            'statistics': collections.Counter(),
            'process': None
        })

        if not worker['process']:
            try:
                worker['process'] = psutil.Process(pid)
            except psutil._error.NoSuchProcess:
                # Message from a "ghost" process
                worker['process'] = None

        if info_type == 'spawn':
            worker['ppid'] = info['worker']['ppid']
        elif info_type == 'request':
            worker['text'] = '{0} {1}'.format(info['method'], info['path'])
            worker['status'] = 'WORK'
        elif info_type == 'response':
            worker['text'] = 'Waiting...'
            worker['statistics'][info['status_code']] += 1
            worker['status'] = 'IDLE'
        elif info_type == 'exit':
            worker['status'] = 'EXIT'
            worker['text'] = 'SIGINT / SIGTERM / SIGQUIT'

    def run(self):
        while not self.stop:
            try:
                text, source = self.socket.recvfrom(8192)
            except:
                time.sleep(PERIOD)
            else:
                self.process(text)
            #time.sleep(PERIOD)

def main():
    listener = ListenerThread(workers)
    listener.start()

    #import locale
    #locale.setlocale(locale.LC_ALL, '')

    try:
        monitor = TabularMonitorWindow(workers)
        monitor.init_screen()
        while not monitor.closing:
            monitor.draw()
            monitor.nap()
        monitor.resetscreen()
    except (KeyboardInterrupt, SystemExit):
        pass

    print 'Waiting for listener to stop...'
    listener.stop = True
    listener.join()
