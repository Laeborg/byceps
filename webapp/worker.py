#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Run a worker for the job queue."""

import sys

from rq import Connection, Queue, Worker

from bootstrap.util import app_context, get_config_name_from_env
from byceps import redis


def get_config_name():
    try:
        return get_config_name_from_env()
    except Exception as e:
        sys.stderr.write(str(e) + '\n')
        sys.exit()


if __name__ == '__main__':
    config_name = get_config_name()

    with app_context(config_name):
        with Connection(redis.get_connection()):
            queues = [Queue()]
            worker = Worker(queues)
            worker.work()
