import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl
import pandas as pd
from tabulate import tabulate
import re
import seaborn as sns
from matplotlib.backends.backend_pdf import PdfPages
import os

mpl.style.use('seaborn-paper')

# each tuple contains: regex, dtype
regex_table = {'intra': '', 'inter': (), 'l2': r'PARTITION_L2_0:(.*):[0-9|\.]+'}
type_table = {'intra': int, 'inter': int, 'l2': float}
metric_label = {'intra': 'Concurrent CTAs/SM',
                'inter': '# of SMs',
                'l2': 'Norm. L2 Partition Size',
                }


# map a panda column from vector cell to scalar cell by taking average
def avg_array(s):
    result = [np.average(np.array(v[1:-1].split(' ')).astype(float)) for v in s]
    return np.array(result)


def process_config_column(*configs, df):
    for c in configs:
        df[c] = df['config'].apply(lambda x: re.search(regex_table[c], x).group(1)).astype(type_table[c])


# required inputs: dataframe, x_column, y_column, z_column, title, axis, cmap, scale
def plot_heatmap(df, x_key, y_key, z_key, title, axis, cmap, scale):
    df.sort_values([y_key, x_key], inplace=True, ascending=[False, True])

    num_cols = len(df[y_key].unique())

    data = np.split(df[z_key].values, num_cols)

    if type_table[z_key] == np.int64:
        fmt = 'd'
    else:
        fmt = '.4f'

    sns.set(font_scale=scale)

    sns.heatmap(data, ax=axis, linewidth=0.2, linecolor='white',
                square=True, cmap=cmap,  # vmin=cbar_lim[0], vmax=cbar_lim[1],
                xticklabels=df[x_key].unique(), yticklabels=df[y_key].unique(),
                annot=True, fmt=fmt,
                cbar_kws={'label': metric_label[z_key]}
                )
    axis.set_xlabel(metric_label[x_key])
    axis.set_ylabel(metric_label[y_key])
    axis.set_title(title)


# required inputs: dataframe, x_key, y_key, legend_key, title, axis, scale
def plot_line(df, x_key, y_key, legend_key, title, axis, scale):
    # Seaborn is being silly with hue of line plot
    # Have to manually add some garbage string at the end so that it's treated as categorical data
    legend_category = legend_key + '_c'
    df[legend_category] = df[legend_key].apply(lambda x: '{0} {1}'.format(x, metric_label[legend_key])) \
                                        .astype('category')

    sns.set(font_scale=scale)

    sns.lineplot(x=x_key, y=y_key, hue=legend_category, data=df, ax=axis)
    axis.set_xlabel(metric_label[x_key])
    axis.set_ylabel(metric_label[y_key])
    axis.set_title(title)
    axis.xaxis.grid()


def plot_intra_inter(df_intra, df_inter, benchmark, figsize, font, inter_valid=True):

    def plot_page_single(pdf, metric_key, metric_name):
        cmap_1 = sns.cubehelix_palette(rot=-.4, dark=0.3, as_cmap=True)

        fig, ((ax1, ax2)) = plt.subplots(1, 2, figsize=figsize)
        fig.suptitle(benchmark + ': ' + metric_name)

        plot_heatmap(df_intra.copy(), regex_x=r'INTRA_0:(.*):0_CTA',
                     label_x='Concurrent CTAs/SM', title='Intra-SM', axis=ax1,
                     cbar=True, cbar_ax=None,
                     cmap=cmap_1, metric_key=metric_key, metric_name=metric_name,
                     font=font,
                     )

        plot_line(df_intra.copy(), regex_legend=r'INTRA_0:(.*):0_CTA',
                  legend='Concurrent CTAs/SM', title='Intra-SM', axis=ax2,
                  metric_key=metric_key, metric_name=metric_name,
                  )

        pdf.savefig(fig)
        plt.close()

    def plot_page_both(pdf, metric_key, metric_name):

        cmap_1 = sns.cubehelix_palette(rot=.1, as_cmap=True)
        cmap_2 = sns.cubehelix_palette(rot=-.4, dark=0.3, as_cmap=True)

        # ignore bypass L2D for now
        def mask(df):
            return df['config'].str.contains('BYPASS_L2D')

        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=figsize)
        fig.suptitle(benchmark + ': ' + metric_name)

        plot_heatmap(df_intra[~mask(df_intra)].copy(), regex_x=r'INTRA_0:(.*):0_CTA',
                     label_x='Concurrent CTAs/SM', title='Intra-SM', axis=ax1,
                     cbar=True, cbar_ax=None,
                     cmap=cmap_1, metric_key=metric_key, metric_name=metric_name, font=font,
                     )
        plot_heatmap(df_inter[~mask(df_inter)].copy(), regex_x=r'INTER_0:(.*):0_SM',
                     label_x='# of SM', title='Inter-SM', axis=ax2,
                     cbar=True, cbar_ax=None,
                     cmap=cmap_2, metric_key=metric_key, metric_name=metric_name, font=font,
                     )
        plot_line(df_intra[~mask(df_intra)].copy(), regex_legend=r'INTRA_0:(.*):0_CTA',
                  legend='Concurrent CTAs/SM', title='Intra-SM', axis=ax3,
                  metric_key=metric_key, metric_name=metric_name,
                  )
        plot_line(df_inter[~mask(df_inter)].copy(), regex_legend=r'INTER_0:(.*):0_SM',
                  legend='# of SM', title='Inter-SM', axis=ax4,
                  metric_key=metric_key, metric_name=metric_name,
                  )

        pdf.savefig(fig)
        plt.close()

    def plot_page(pdf, metric_key, metric_name):
        if inter_valid:
            plot_page_both(pdf, metric_key, metric_name)
        else:
            plot_page_single(pdf, metric_key, metric_name)

    # scale all IPC to baseline
    baseline = df_seq[df_seq['pair_str'] == benchmark]['ipc'].values[0]
    df_intra['norm_ipc'] = df_intra['ipc'] / baseline

    df_intra['avg_dram_bw'] = df_intra['dram_bw'].transform(avg_array)

    # calculate DRAM idleness
    df_intra['dram_idleness'] = np.divide(df_intra['mem_idle'].transform(avg_array),
                                          df_intra['total_cmd'].transform(avg_array))

    if inter_valid:
        df_inter['norm_ipc'] = df_inter['ipc'] / baseline
        df_inter['avg_dram_bw'] = df_inter['dram_bw'].transform(avg_array)

        # calculate DRAM idleness
        df_inter['dram_idleness'] = np.divide(df_inter['mem_idle'].transform(avg_array),
                                              df_inter['total_cmd'].transform(avg_array))

    filename = '{0}-{1}.pdf'.format(benchmark, 'both' if inter_valid else 'intra')
    filename = os.path.join('plots', filename)
    with PdfPages(filename) as pdf:
        plot_page(pdf, 'norm_ipc', 'Normalized IPC')
        plot_page(pdf, 'avg_dram_bw', 'DRAM Bandwidth Utilization')
        plot_page(pdf, 'dram_idleness', 'DRAM IDLE RATE')
        plot_page(pdf, 'l2_miss_rate', 'L2 Miss Rate')
        plot_page(pdf, 'l2_BW', 'L2 Bandwidth')
        plot_page(pdf, 'l2_total_accesses', 'L2 Total Accesses')
        plot_page(pdf, 'l1D_miss_rate', 'L1 Miss Rate')
        plot_page(pdf, 'avg_mem_lat', 'Average Memory Latency')

    return df_intra
