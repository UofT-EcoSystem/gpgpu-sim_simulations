import os
import subprocess

from constant import *

config_str = "TITANV-SEP_RW"
jobname = 'seq'

for benchmark in app_dict:
    p = subprocess.run(['python',
                        os.path.join(RUN_HOME, 'run_simulations.py'),
                        '-B', benchmark,
                        '-C', config_str,
                        '-E', DEFAULT_BENCH_HOME,
                        '-N', jobname,
                        ],
                       stdout=subprocess.PIPE)

    print(p.stdout.decode("utf-8"))


