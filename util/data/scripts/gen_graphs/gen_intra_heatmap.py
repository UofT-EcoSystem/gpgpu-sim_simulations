import matplotlib.backends.backend_pdf
import os
from matplotlib.backends.backend_pdf import PdfPages
import argparse
import pandas as pd
import matplotlib.pyplot as plt

import common.help_iso as hi
import common.constants as const


def print_intra(df, benchmark):
    filename = '{0}-{1}.pdf'.format(benchmark, 'intra')
    filename = os.path.join(const.DATA_HOME, 'graphs', filename)
    with PdfPages(filename) as pdf:
        hi.plot_page_intra(df, 'norm_ipc', benchmark, pdf)
        hi.plot_page_intra(df, 'avg_dram_bw', benchmark, pdf)
        hi.plot_page_intra(df, 'dram_busy', benchmark, pdf)
        hi.plot_page_intra(df, 'l2_miss_rate', benchmark, pdf)
        hi.plot_page_intra(df, 'l2_BW', benchmark, pdf)
        hi.plot_page_intra(df, 'l2_total_accesses', benchmark, pdf)
        hi.plot_page_intra(df, 'l1D_miss_rate', benchmark, pdf)
        hi.plot_page_intra(df, 'avg_mem_lat', benchmark, pdf)


def print_intra_inter(df_intra, df_inter, benchmark):
    filename = '{0}-{1}.pdf'.format(benchmark, 'both')
    filename = os.path.join('plots', filename)
    with PdfPages(filename) as pdf:
        hi.plot_page_intra_inter(df_intra, df_inter, 'norm_ipc', benchmark, pdf)


def parse_args():
    parser = argparse.ArgumentParser('Generate heatmaps for intra runs.')
    parser.add_argument('--pickle',
                        default=os.path.join(const.DATA_HOME, 'pickles/intra.pkl'),
                        help='Pickle that stores all the intra info.')
    parser.add_argument('--content', choices=['metrics', 'ipc'],
                        default='ipc',
                        help='metrics: print all relevant metrics per benchmark. ipc: print IPC heatmaps only.')
    parser.add_argument('--benchmark',
                        default='all',
                        nargs='+',
                        help='Individual benchmark to print heatmaps')
    parser.add_argument('--subplots',
                        nargs='+',
                        type=int,
                        help='Dimension of subplots in plots. Expect two values for height and width. '
                             'Only used for ipc only mode')
    parser.add_argument('--figsize',
                        nargs='+',
                        type=int,
                        default=[30, 30],
                        help='Dimension of the figure. Used for ipc only mode.')

    results = parser.parse_args()
    return results


def print_ipc_only(df, benchmarks, subplots, figsize):
    print(benchmarks)
    fig_tot, axs = plt.subplots(subplots[0], subplots[1], figsize=figsize)
    axs = axs.flat

    for ax, bench in zip(axs, benchmarks):
        _df = df[df['pair_str'] == bench]

        hi.plot_heatmap(_df, x_key='intra', y_key='l2', z_key='norm_ipc', title=bench, axis=ax, scale=1.2)

    fig_tot.suptitle('Intra, Normalized IPC', fontsize=18)
    fig_tot.savefig(os.path.join(const.DATA_HOME, 'graphs/total.pdf'))
    plt.close()


def main():
    args = parse_args()

    df_intra = pd.read_pickle(args.pickle)
    df_intra.sort_values('pair_str', inplace=True)

    if args.benchmark[0] == 'all':
        bench_list = df_intra['pair_str'].unique()
        args.benchmark = bench_list

    if args.content == 'metrics':
        for bench in args.benchmark:
            print_intra(df_intra, bench)
    elif args.content == 'ipc':
        if not args.subplots:
            args.subplots = [len(args.benchmark), 1]

        print_ipc_only(df_intra, args.benchmark, args.subplots, tuple(args.figsize))


if __name__ == '__main__':
    main()
