import argparse
import subprocess
import os
import pandas as pd
import numpy as np
import sys

DEFAULT_BENCH_HOME = "/mnt/GPU-Virtualization-Benchmarks/benchmarksv2"
RUN_HOME = os.path.join(os.path.dirname(os.path.realpath(__file__)), '..')
NUM_SM = 80


def parse_args():
    parser = argparse.ArgumentParser("Run app in isolation mode \
            and sweep resource sizes.")

    parser.add_argument('--apps', required=True, nargs='+', help="Apps to run.")
    parser.add_argument('--bench_home', default=DEFAULT_BENCH_HOME, help='Benchmark home folder.')
    parser.add_argument('--cta_step', default=1, help='Sweeping step of CTAs/SM for intra-SM sharing.')
    parser.add_argument('--sm_step', default=1, help='Sweeping step of SMs for inter-SM sharing.')

    results = parser.parse_args()

    return results


# max ctas according to resource constraints, grid size
app_dict = {'cut_sgemm-0': [2, 128],
            'cut_sgemm-1': [2, 512],
            'cut_wmma-0': [4, 128],
            'cut_wmma-1': [4, 1024],
            'parb_sgemm-0': [11, 528],
            'parb_cutcp-0': [16, 121],
            'parb_stencil-0': [16, 1024],
            'parb_lbm-0': [12, 18000],
            'parb_spmv-0': [16, 1147],
            }

app_df = pd.DataFrame.from_dict(app_dict, orient='index',
                                columns=['max_cta', 'grid'])
app_df['achieved_cta'] = pd.DataFrame([np.ceil(app_df['grid'] / 80),
                                       app_df['max_cta']]).min().astype('int32')
app_df['achieved_sm'] = np.ceil(app_df['grid'] / app_df['max_cta']) \
    .astype('int32')

mem_intense = ['parb_stencil-0', 'parb_lbm-0', 'parb_spmv-0']

args = parse_args()

for app in args.apps:
    if app not in app_df.index.values:
        print("{0} is not in application map. Skip.".format(app))

    base_config = "TITANV-SEP_RW-CONCURRENT"
    intra_sm = ["INTRA_0:{0}:0_CTA".format(i)
                for i in range(args.cta_step, app_df.loc[app, 'achieved_cta'] + 1, args.cta_step)]
    inter_sm = ["INTER_0:{0}:0_SM".format(i)
                for i in range(args.sm_step, app_df.loc[app, 'achieved_sm'] + 1, args.sm_step)]

    l2_fract = [0.125, 0.25, 0.5, 1.0]
    l2_partition = ["PARTITION_L2_0:{0}:{1}".format(f, 1 - f) for f in l2_fract]

    bypass_l2d = "BYPASS_L2D_S1"


    def launch_job(sm_config, jobname):
        configs = ["-".join([base_config, sm, l2])
                   for sm in sm_config for l2 in l2_partition]
        if app in mem_intense:
            configs = configs + [c + '-' + bypass_l2d for c in configs]

        config_str = ','.join(configs)

        p = subprocess.run(['python',
                            os.path.join(RUN_HOME, 'run_simulations.py'),
                            '-B', app,
                            '-C', config_str,
                            '-E', DEFAULT_BENCH_HOME,
                            '-r', os.path.join(DEFAULT_BENCH_HOME, 'run-' + jobname),
                            '-N', jobname,
                            ],
                           stdout=subprocess.PIPE)

        print(p.stdout.decode("utf-8"))


    # 1. launch isolation_intra job
    launch_job(intra_sm, 'isolation-intra')
    # 2. launch isolation_inter job
    launch_job(inter_sm, 'isolation-inter')
