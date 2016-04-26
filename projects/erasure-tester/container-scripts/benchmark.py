#!/usr/bin/env python3
import json
import logging
import socket
import subprocess
from datetime import datetime

import pydevd as pydevd
import signal
import sys
from time import sleep

from benchmarks_impl import BenchmarksImpl
from redis_cluster import RedisCluster
from utils import kill_pid


class Benchmarks:
    log_file_base = '/opt/erasuretester/results/result_'

    def __init__(self):
        # 2 is forbidden due to Redis limitation on Cluster size
        self.redis_size = [15, 60, 100]
        self.erasure_codes = ['Null', 'ReedSolomon', 'SimpleRegenerating']
        self.erasure_configs = {
            'ReedSolomon': [
                (10, 4, 0)
            ],
            'SimpleRegenerating': [
                (10, 6, 5)
            ],
            'Null': [
                (10, 0, 0)
            ]
        }
        self.first = True
        self.results = []
        self.log_file_base += datetime.today().isoformat()

        benchmarks_impl = BenchmarksImpl('/mnt/erasure/')
        self.benches = [getattr(benchmarks_impl, m) for m in dir(benchmarks_impl) if m.startswith('bench_')]

    def run_benchmarks(self):
        for rs in self.redis_size:
            for ec in self.erasure_codes:
                for (ss, ps, src) in self.erasure_configs[ec]:
                    for b in self.benches:
                        with RedisCluster(rs) as redis:
                            sb = 'Jedis' if rs > 0 else 'Memory'
                            config = [ec, rs, sb, ss, ps, src]
                            print("Running with " + str(config))
                            (params, env) = self._get_java_params(redis, *config)
                            with JavaProgram(params, env) as java:
                                try:
                                    self._run_benchmark(b, config, redis, java)
                                except Exception as ex:
                                    logging.exception("The benchmark crashed, continuing with the rest...")
                        self.save_results_to_file()

    def _run_benchmark(self, bench, config, redis, java):
        bench_name = bench.__name__
        print("    " + bench_name)
        self.results.append({
            'bench': bench_name,
            'config': config,
            'results': bench(config, redis, java)
        })

    def save_results_to_file(self):
        with open(self.log_file_base + '.json', 'w') as out:
            json.dump(self.results, out, indent=4)

    @staticmethod
    def _get_java_params(redis, erasure, redis_size, storage, stripe=None, parity=None, src=None, quiet=True):
        params = [
            '--erasure-code', erasure,
            '--storage', storage
        ]
        if quiet:
            params += ['-q']
        if stripe is not None:
            params += ['--stripe', str(stripe)]
        if parity is not None:
            params += ['--parity', str(parity)]
        if src is not None:
            params += ['--src', str(src)]
        if redis_size > 1:
            params += ['--redis-cluster']

        env = {'REDIS_ADDRESS': redis.get_master_node_str(redis_size)} if redis_size > 0 else {}
        return params, env


class JavaProgram:
    java_with_args = ["java"]
    # java_with_args += ["-agentlib:jdwp=transport=dt_socket,server=n,address=172.16.0.167:5005,suspend=y"]
    java_with_args += "-Xmx6G -cp * ch.unine.vauchers.erasuretester.Main /mnt/erasure".split(' ')
    proc = None

    def __init__(self, more_args, env):
        self.more_args = more_args
        self.env = env

    def __enter__(self):
        self.proc = subprocess.Popen(self.java_with_args + self.more_args, env=self.env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, stdin=subprocess.PIPE)
        sleep(10)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        kill_pid(self.proc)

    def flush_read_cache(self):
        self.proc.stdin.write(b"clearCache\n")
        self._wait_command_completion()

    def repair_all_files(self):
        self.proc.stdin.write(b"repairAll\n")
        self._wait_command_completion()

    def repair_file(self, filepath):
        self.proc.stdin.write(("repair %s\n" % filepath).encode())
        self._wait_command_completion()

    def _wait_command_completion(self):
        self.proc.stdout.flush()
        self.proc.stdin.flush()
        limit = 3
        while limit > 0 and self.proc.stdout.readline() != b"Done\n":
            limit -= 1
            print("Waiting for the command to complete...")
        if limit <= 0:
            print("The command did not complete!")


if __name__ == '__main__':
    print("Ready, waiting 60 seconds")
    sleep(60)
    try:
        i = 1
        while True:
            ip = socket.getaddrinfo('erasuretester_benchmark_%d' % i, 6379, socket.AF_INET)[0][4][0]

            try:
                subprocess.check_call(('ping -c 1 -W 3 %s' % ip).split(' '))
                print("%d OK" % i)
            except subprocess.CalledProcessError:
                print("%d KO" % i)

            i += 1
    except socket.gaierror:
        pass
    print("Finished")
    sleep(60)
