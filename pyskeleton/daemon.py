#!/usr/bin/env python
import sys
import os
import subprocess
import atexit
import logging
import argparse


LOG = logging.getLogger(__name__)


def create_optparser():
    argument_parser = argparse.ArgumentParser()
    argument_parser.add_argument(
        '-c', '--config',
        help='Absolute path to configuration file',
        default='/etc/pyskeleton/skeleton.yaml',
    )
    argument_parser.add_argument(
        '-d', '--daemonize',
        action='store_true',
        help='Specifies if pyskeleton should be ran as independent process'
    )
    argument_parser.add_argument(
        '--pid-file',
        help='Specifies where to store pid',
        default='/var/run/pyskeleton/pyskeleton.pid',
    )
    argument_parser.add_argument(
        '--error-log',
        help='Specifies where stdout and stderr will be redirected '
             'if skeleton is running as independent process',
        default='/var/log/pyskeleton/pyskeleton.err',
    )

    return argument_parser


def daemonize(pid_file, error_log):
    if os.path.exists(pid_file):
        raise RuntimeError("Pid file {0} already exists".format(pid_file))

    def redirect_stream(system_stream, target_stream):
        os.dup2(target_stream.fileno(), system_stream.fileno())

    def fork_exit_parent():
        pid = os.fork()
        if pid > 0:
            os._exit(0)

    def close_all_open_files():
        '''Close all file descriptors except for stdin, stdout, stderr'''
        os.closerange(3, subprocess.MAXFD)

    fork_exit_parent()
    os.chdir('/')
    os.setsid()
    os.umask(027)
    close_all_open_files()
 
    # redirect standard file descriptors
    with open(os.devnull) as devnull:
        redirect_stream(sys.stdin, devnull)

    with open(error_log, 'a') as error_log_file:
        redirect_stream(sys.stdout, error_log_file)
        redirect_stream(sys.stderr, error_log_file)
       
    with open(pid_file, 'w') as f:
        f.write(str(os.getpid()))

    atexit.register(lambda: os.remove(pid_file))
