#!/usr/bin/env python3


import sys
import os
import time
import pandas as pd
import numpy as np
from matplotlib import pyplot as plt
import matplotlib.ticker as mtick
import seaborn as sns
import play_a_game

from bokeh.io import output_notebook, output_file, show
from bokeh.models import CustomJS, ColumnDataSource, Range1d, \
    LinearAxis, Div, Arrow, NormalHead, Label, Span, \
    Legend, DataTable, TableColumn, NumberFormatter, NumeralTickFormatter
from bokeh.plotting import figure, Figure
from bokeh.models.widgets import Slider
from bokeh.layouts import row, column, gridplot, grid
#tools for create/launch html file
from bokeh.resources import CDN
from bokeh.embed import file_html
import webbrowser, os


# Declare styling for data viz
normal_color = '#74D1EA'
malicious_color = '#FFA38B'
fp_color = '#A8C0BB'
fn_color = '#FA4616'
precision_color = '#E40046'
recall_color = '#00C1D4'
f1_color = '#87037B'
total_weighted_color = '#00C65E'
title_font_size = '18pt'
cell_bg_color = '#DAD9D6'
cell_bg_alpha = .4
plot_bg_alpha = .15
left_border = 40
right_border = 40
top_border = 60
bottom_border = 40

# Read CSV to pandas while performing some error checking
def file_to_df(path):
    try:
        # Read csv to Pandas DataFrame object
        df = pd.read_csv(path)
        return df
    # Wrong path check
    except FileNotFoundError:
        print('We could not find or read your file.')
        print('Please check your relative path.')
        # Exit script
        sys.exit()


# Let the user enter a number index to avoid spelling errors
def columns_picker(cols_lst):
    metric = cols_lst[int(input('Please select the index number of the metric field: '))]
    indicator = cols_lst[int(input('Please select the index number of the malicious event indicator field: '))]
    print(f'''You will be placing a threshold on \"{metric}\"
and the malicious event indicator is \"{indicator}\".
''')
    return metric, indicator


# Split out the normal vs malicious samples as Pandas Series
def classification_split(df, metric_col, indicator_col):
    # Filter for True (1) indicators of malicious activity and select the metric column.
    malicious = df.loc[df[indicator_col] == 1, metric_col]. \
        copy().reset_index(drop=True)

    # Filter for 0 to get normal traffic.
    normal = df.loc[df[indicator_col] == 0, metric_col]. \
        copy().reset_index(drop=True)

    return malicious, normal


# Threshold-generating utility
def threshold_calc(mean, stddev, multiplier):
    return mean + (stddev * multiplier)


# Generate confusion matrix and accuracy scores based on a threshold
def confusion_matrix(mal_series, norm_series, threshold):
    mal_lst = mal_series.tolist()
    norm_lst = norm_series.tolist()
    true_positives = len([i for i in mal_lst if i >= threshold])
    false_positives = len([i for i in norm_lst if i >= threshold])
    true_negatives = len(norm_lst) - false_positives
    false_negatives = len(mal_lst) - true_positives

    precision = true_positives / (true_positives + false_positives)
    recall = true_positives / (true_positives + false_negatives)
    f1_score = 2 * (precision * recall) / (precision + recall)

    outcome_dict = {
        'TP': true_positives,
        'FP': false_positives,
        'TN': true_negatives,
        'FN': false_negatives,
        'precision': precision,
        'recall': recall,
        'f1_score': f1_score
    }

    return outcome_dict


# If it doesn't exist, make an app folder to hold any exports.
def make_folder(folder_name):
    home = os.path.expanduser('~')
    # Check if there's an app folder
    app_path = os.path.join(home, 'cream')
    if not os.path.isdir(app_path):
        os.mkdir(app_path)
        print(f'Created app folder at: {app_path}')
    session_folder = os.path.join(app_path, folder_name)
    if not os.path.isdir(session_folder):
        os.mkdir(session_folder)
        print(f'Created project folder at: {session_folder}')
    else:
        print('This folder already exists.')
    return session_folder


# Generate DataFrame with simulated results of various thresholds.
def monte_carlo(mal_series, norm_series, norm_mean, norm_stddev, mult_lst):
    evaluations = {}
    for mult in mult_lst:
        threshold = threshold_calc(norm_mean, norm_stddev, mult)
        evaluations[mult] = confusion_matrix(mal_series, norm_series, threshold)
    eval_df = pd.DataFrame.from_dict(evaluations, orient='index'). \
        reset_index().rename(columns={'index': 'multiplier'})
    return eval_df


def main():
    print('''Please select the CSV dataset you\'d like to use.
    The dataset should contain these columns:
        - metric to apply threshold to
        - indicator of event to detect (e.g. malicious activity)
            - Please label this as 1 or 0 (true or false); 
            This will not work otherwise!
    ''')

    file_path = input('Enter the path of your dataset: ')
    imported_data = file_to_df(file_path)
    time.sleep(1)

    print(f'''\nGreat! Here is a preview of your data:
Imported fields:''')
    # List headers by column index.
    cols = list(imported_data.columns)
    for index in range(len(cols)):
        print(f'{index}: {cols[index]}')
    print(f'Number of records: {len(imported_data.index)}\n')
    # Preview the DataFrame
    time.sleep(1)
    print(imported_data.head(), '\n')

    # Prompt for the metric and source of truth.
    time.sleep(1)
    metric_col, indicator_col = columns_picker(cols)
    # User self-validation.
    col_check = input('Can you confirm if this is correct? (y/n): ').lower()
    # If it's wrong, let them try again
    while col_check != 'y':
        metric_col, indicator_col = columns_picker(cols)
        col_check = input('Can you confirm if this is correct? (y/n): ').lower()
    else:
        print('''\nGreat! Thanks for your patience.
Generating summary stats now..\n''')

    # Generate summary stats.
    time.sleep(1)
    malicious, normal = classification_split(imported_data, metric_col, indicator_col)
    mal_mean = malicious.mean()
    mal_stddev = malicious.std()
    mal_count = malicious.size
    mal_median = malicious.median()
    norm_mean = normal.mean()
    norm_stddev = normal.std()
    norm_count = normal.size
    norm_median = normal.median()

    print(f'''Normal vs Malicious Summary (metric = {metric_col}):
Normal:
-----------------------------
Observations: {round(norm_count, 2)}
Average: {round(norm_mean, 2)}
Median: {round(norm_median, 2)}
Standard Deviation: {round(norm_stddev, 2)}

Malicious:
-----------------------------
Observations: {round(mal_count, 2)}
Average: {round(mal_mean, 2)}
Median: {round(mal_median, 2)}
Standard Deviation: {round(mal_stddev, 2)}
''')

    # Insights and advisories
    # Provide the accuracy metrics of a generic threshold at avg + 3 std deviations
    generic_threshold = confusion_matrix(malicious, normal, threshold_calc(norm_mean, norm_stddev, 3))

    time.sleep(1)
    print(f'''A threshold at (average + 3x standard deviations) {metric_col} would result in:
    - True Positives (correctly identified malicious events: {generic_threshold['TP']:,}
    - False Positives (wrongly identified normal events: {generic_threshold['FP']:,}
    - True Negatives (correctly identified normal events: {generic_threshold['TN']:,}
    - False Negatives (wrongly identified malicious events: {generic_threshold['FN']:,}

    Accuracy Metrics:
    - Precision (what % of events above threshold are actually malicious): {round(generic_threshold['precision'] * 100, 1)}%
    - Recall (what % of malicious events did we catch): {round(generic_threshold['recall'] * 100, 1)}%
    - F1 Score (blends precision and recall): {round(generic_threshold['f1_score'] * 100, 1)}%''')

    # Distribution skew check.
    if norm_mean >= (norm_median * 1.1):
        time.sleep(1)
        print(f'''\nYou may want to be cautious as your normal traffic\'s {metric_col} 
has a long tail towards high values. The median is {round(norm_median, 2)} 
compared to {round(norm_mean, 2)} for the average.''')

    if mal_mean < threshold_calc(norm_mean, norm_stddev, 2):
        time.sleep(1)
        print(f'''\nWarning: you may find it difficult to avoid false positives as the average
{metric_col} for malicious traffic is under the 95th percentile of the normal traffic.''')

    # For fun/anticipation. Actually a nerd joke because of the method we'll be using.
    if '-q' not in sys.argv[1:]:
        time.sleep(1)
        play_a_game.billy()
        decision = input('yes/no: ').lower()
        while decision != 'yes':
            time.sleep(1)
            print('...That\'s no fun...')
            decision = input('Let\'s try that again: ').lower()

    # Let's get to the simulations!
    time.sleep(1)
    print('''\nInstead of manually experimenting with threshold multipliers, 
let\'s simulate a range of options and see what produces the best result. 
This is known as \"Monte Carlo simulation\".\n''')

    # Initialize session name & create app folder if there isn't one.
    time.sleep(1)
    session_name = input('Please provide a name for this project/session: ')
    session_folder = make_folder(session_name)

    # Generate list of multipliers to iterate over.
    time.sleep(1)
    mult_start = float(input('Please provide the minimum multiplier you want to start at. We recommend 2: '))
    # Set the max to how many std deviations away the sample max is.
    mult_end = (imported_data[metric_col].max() - norm_mean) / norm_stddev
    mult_interval = float(input('Please provide the desired gap between multiplier options: '))
    # range() only allows integers, let's manually populate a list
    multipliers = []
    mult_counter = mult_start
    while mult_counter < mult_end:
        multipliers.append(round(mult_counter, 2))
        mult_counter += mult_interval
    print('Generating simulations..\n')

    # Run simulations using our multipliers.
    simulations = monte_carlo(malicious, normal, norm_mean, norm_stddev, multipliers)
    print('Done!')
    time.sleep(1)

    # Save simulations as CSV for later use.
    simulation_filepath = os.path.join(session_folder, f'{session_name}_simulation_results.csv')
    simulations.to_csv(simulation_filepath, index=False)
    print(f'Saved results to: {simulation_filepath}')
    # Find the first threshold with the highest F1 score.
    # This provides a balanced approach between precision and recall.
    f1_max = simulations[simulations.f1_score == simulations.f1_score.max()].head(1)
    f1_max_mult = f1_max.squeeze()['multiplier']
    time.sleep(1)
    print(f'''\nBased on the F1 score metric, setting a threshold at {round(f1_max_mult,1)} standard deviations
above the average magnitude might provide optimal results.\n''')
    time.sleep(1)
    print(f'''{f1_max}

We recommend that you skim the CSV and the following visualization outputs 
to sanity check results and make your own judgement.
''')

    # Now for the fun part..generating the visualizations via Bokeh.
    output_file(os.path.join(session_folder, f'{session_name}_overview.html'))

    # List of Bokeh objects to render.
    bokeh_objects = []

    # Summary stats from earlier.
    summary_text = f'''
    <h1>Results Overview</h1> 
    <i>metric = magnitude</i>

    <table style="width:100%,text-align: right">
      <tr>
        <th style="text-align:left">Metric</th>
        <th style="text-align:left">Normal Events</th>
        <th style="text-align:left">Malicious Events</th>
      </tr>
      <tr>
        <td style="text-align:left">Observations</td>
        <td style="text-align:left">{norm_count:,}</td>
        <td style="text-align:left">{mal_count:,}</td>
      </tr>
      <tr>
        <td style="text-align:left">Average</td>
        <td style="text-align:left">{round(norm_mean, 2):,}</td>
        <td style="text-align:left">{round(mal_mean, 2):,}</td>
      </tr>
      <tr>
        <td style="text-align:left">Median</td>
        <td style="text-align:left">{round(norm_median, 2):,}</td>
        <td style="text-align:left">{round(mal_median, 2):,}</td>
      </tr> 
      <tr>
        <td style="text-align:left">Standard Deviation</td>
        <td style="text-align:left">{round(norm_stddev, 2):,}</td>
        <td style="text-align:left">{round(mal_stddev, 2):,}</td>
      </tr> 
    </table>
    '''
    title_text = '''
    <style>
    custom_1 {
    color: #EACBBB;
    font-size: 80px;
    font-style: bold;
    font-family: "Helvetica Neue", Helvetica, Roboto, sans-serif;
    font-weight: 700;
    }
    </style>
    <custom_1>Cream.</custom_1>
    '''
    title_div = Div(text=title_text, width=800, height=80, margin=(10,0,50,65))
    bokeh_objects.append(title_div)


    summary_div = Div(text=summary_text, width=900, height=200, align='start', margin=(0, -500, 0, 70))
    bokeh_objects.append(summary_div)

    # Results of the hypothetical threshold.
    hypothetical = f'''
    <h2>"Rule of thumb" hypothetical</h2>
    <p>A threshold at <i>(average + 3x standard deviations)</i> {metric_col} would result in:</p>
    <ul>
        <li>True Positives (correctly identified malicious events: 
            <b>{generic_threshold['TP']:,}</b></li>
        <li>False Positives (wrongly identified normal events:
            <b>{generic_threshold['FP']:,}</b></li>
        <li>True Negatives (correctly identified normal events: 
            <b>{generic_threshold['TN']:,}</b></li>
        <li>False Negatives (wrongly identified malicious events: 
            <b>{generic_threshold['FN']:,}</b></li>
    </ul>
    <h3>Accuracy Metrics</h3>
    <ul>
        <li>Precision (what % of events above threshold are actually malicious): 
            <b>{round(generic_threshold['precision'] * 100, 1)}</b></li>
        <li>Recall (what % of malicious events did we catch): 
            <b>{round(generic_threshold['recall'] * 100, 1)}</b></li>
        <li>F1 Score (blends precision and recall): 
            <b>{round(generic_threshold['f1_score'] * 100, 1)}</b></li>
    </ul>
    '''

    hypo_div = Div(text=hypothetical, width=900, height=350, margin=(5,0,0,-600))
    bokeh_objects.append(hypo_div)

    # Let's get the exploratory charts generated.

    malicious_hist, malicious_edge = np.histogram(malicious, bins=100)
    mal_hist_df = pd.DataFrame({
        'metric': malicious_hist,
        'left': malicious_edge[:-1],
        'right': malicious_edge[1:]
    })

    normal_hist, normal_edge = np.histogram(normal, bins=100)
    norm_hist_df = pd.DataFrame({
        'metric': normal_hist,
        'left': normal_edge[:-1],
        'right': normal_edge[1:]
    })

    exploratory = figure(plot_width=800, plot_height=500, sizing_mode='scale_width',
                         title=f'{metric_col.capitalize()} Distribution',
                         x_axis_label=f'{metric_col.capitalize()}',
                         y_axis_label='Observations'
                         )

    exploratory.title.text_font_size = title_font_size
    exploratory.border_fill_color = cell_bg_color
    exploratory.border_fill_alpha = cell_bg_alpha
    exploratory.background_fill_color = cell_bg_color
    exploratory.background_fill_alpha = plot_bg_alpha
    exploratory.min_border_left = left_border
    exploratory.min_border_right = right_border
    exploratory.min_border_top = top_border
    exploratory.min_border_bottom = bottom_border

    exploratory.quad(bottom=0, top=mal_hist_df.metric, left=mal_hist_df.left, right=mal_hist_df.right,
                     legend_label='malicious', fill_color=malicious_color, alpha=.85)
    exploratory.quad(bottom=0, top=norm_hist_df.metric, left=norm_hist_df.left, right=norm_hist_df.right,
                     legend_label='normal', fill_color=normal_color, alpha=.35)

    exploratory.add_layout(Arrow(end=NormalHead(fill_color=malicious_color, size=10, line_alpha=0),
                                 line_color=malicious_color, x_start=mal_mean,
                                 y_start=mal_count, x_end=mal_mean, y_end=0))
    arrow_label = Label(x=mal_mean, y=mal_count * 1.2, text='Malicious Events')

    exploratory.add_layout(arrow_label)
    exploratory.xaxis.formatter = NumeralTickFormatter(format='0,0')
    exploratory.yaxis.formatter = NumeralTickFormatter(format='0,0')

    # 3 sigma reference line
    thresh = Span(location=threshold_calc(norm_mean, norm_stddev, 3), dimension='height', line_color='grey',
                  line_dash='dashed', line_width=2)
    exploratory.add_layout(thresh)

    thresh_label = Label(x=norm_mean + (norm_stddev * 3.05), y=400, y_units='screen',
                         text='3 Std Dev Threshold', text_font_style='bold')
    exploratory.add_layout(thresh_label)

    exploratory.legend.location = "top_right"
    bokeh_objects.append(exploratory)

    # Zoomed in version
    overlap_view = figure(plot_width=800, plot_height=500, sizing_mode='scale_width',
                          title=f'Overlap Highlight',
                          x_axis_label=f'{metric_col.capitalize()}',
                          y_axis_label='Observations',
                          y_range=(0, mal_count * .33),
                          x_range=(norm_mean + (norm_stddev * 2.5), mal_mean + (mal_stddev * 3)),
                          )

    overlap_view.title.text_font_size = title_font_size
    overlap_view.border_fill_color = cell_bg_color
    overlap_view.border_fill_alpha = cell_bg_alpha
    overlap_view.background_fill_color = cell_bg_color
    overlap_view.background_fill_alpha = plot_bg_alpha
    overlap_view.min_border_left = left_border
    overlap_view.min_border_right = right_border
    overlap_view.min_border_top = top_border
    overlap_view.min_border_bottom = bottom_border

    overlap_view.quad(bottom=0, top=mal_hist_df.metric, left=mal_hist_df.left, right=mal_hist_df.right,
                      legend_label='malicious', fill_color=malicious_color, alpha=.85)
    overlap_view.quad(bottom=0, top=norm_hist_df.metric, left=norm_hist_df.left, right=norm_hist_df.right,
                      legend_label='normal', fill_color=normal_color, alpha=.35)
    overlap_view.xaxis.formatter = NumeralTickFormatter(format='0,0')
    overlap_view.yaxis.formatter = NumeralTickFormatter(format='0,0')

    thresh_label = Label(x=threshold_calc(norm_mean, norm_stddev, 3), y=mal_count * .33 * .95,
                         text='3 Std Dev Threshold')
    overlap_view.add_layout(thresh)
    overlap_view.add_layout(thresh_label)

    overlap_view.legend.location = "top_right"
    bokeh_objects.append(overlap_view)

    # Probability Density
    malicious_hist_dense, malicious_edge_dense = np.histogram(malicious, density=True, bins=33)
    mal_hist_dense_df = pd.DataFrame({
        'metric': malicious_hist_dense,
        'left': malicious_edge_dense[:-1],
        'right': malicious_edge_dense[1:]
    })

    normal_hist_dense, normal_edge_dense = np.histogram(normal, density=True, bins=100)
    norm_hist_dense_df = pd.DataFrame({
        'metric': normal_hist_dense,
        'left': normal_edge_dense[:-1],
        'right': normal_edge_dense[1:]
    })

    density = figure(plot_width=800, plot_height=500, sizing_mode='scale_width',
                     title='Probability Density',
                     x_axis_label=f'{metric_col.capitalize()}',
                     y_axis_label='% of Group Total'
                     )

    density.title.text_font_size = title_font_size
    density.border_fill_color = cell_bg_color
    density.border_fill_alpha = cell_bg_alpha
    density.background_fill_color = cell_bg_color
    density.background_fill_alpha = plot_bg_alpha
    density.min_border_left = left_border
    density.min_border_right = right_border
    density.min_border_top = top_border
    density.min_border_bottom = bottom_border

    density.quad(bottom=0, top=mal_hist_dense_df.metric, left=mal_hist_dense_df.left,
                 right=mal_hist_dense_df.right, legend_label='malicious', fill_color=malicious_color, alpha=.85)
    density.quad(bottom=0, top=norm_hist_dense_df.metric, left=norm_hist_dense_df.left,
                 right=norm_hist_dense_df.right, legend_label='normal', fill_color=normal_color, alpha=.35)
    density.xaxis.formatter = NumeralTickFormatter(format='0,0')
    density.yaxis.formatter = NumeralTickFormatter(format='0.000%')

    density.add_layout(thresh)
    density.add_layout(thresh_label)

    density.legend.location = "top_right"
    bokeh_objects.append(density)

    # Simulation Series to be used
    false_positives = simulations.FP
    false_negatives = simulations.FN
    multiplier = simulations.multiplier
    precision = simulations.precision
    recall = simulations.recall
    f1_score = simulations.f1_score
    f1_max = simulations[simulations.f1_score == simulations.f1_score.max()].head(1).squeeze()['multiplier']

    # False Positives vs False Negatives
    errors = figure(
        plot_width=800,
        plot_height=500,
        sizing_mode='scale_width',
        x_range=(multiplier.min(), multiplier.max()),
        y_range=(0, false_positives.max()),
        title='False Positives vs False Negatives',
        x_axis_label='Multiplier',
        y_axis_label='Count'
    )

    errors.title.text_font_size = title_font_size
    errors.border_fill_color = cell_bg_color
    errors.border_fill_alpha = cell_bg_alpha
    errors.background_fill_color = cell_bg_color
    errors.background_fill_alpha = plot_bg_alpha
    errors.min_border_left = left_border
    errors.min_border_right = right_border
    errors.min_border_top = top_border
    errors.min_border_bottom = right_border

    errors.line(multiplier, false_positives, legend_label='false positives', line_width=2, color=fp_color)
    errors.line(multiplier, false_negatives, legend_label='false negatives', line_width=2, color=fn_color)
    errors.yaxis.formatter = NumeralTickFormatter(format='0,0')

    errors.extra_y_ranges = {"y2": Range1d(start=0, end=1.1)}
    errors.add_layout(LinearAxis(y_range_name="y2", axis_label="Score",
                                 formatter=NumeralTickFormatter(format='0.00%')), 'right')
    errors.line(multiplier, f1_score, line_width=2,
                color=f1_color, legend_label='F1 Score', y_range_name="y2")

    # F1 Score Maximization point
    f1_thresh = Span(location=f1_max, dimension='height', line_color=f1_color,
                     line_dash='dashed', line_width=2)
    f1_label = Label(x=f1_max + .05, y=200, y_units='screen', text=f'F1 Max: {round(f1_max,2)}',
                     text_font_size='10pt', text_font_style='bold',
                     text_align='left', text_color=f1_color)

    errors.add_layout(f1_thresh)
    errors.add_layout(f1_label)

    errors.legend.location = "top_right"
    errors.legend.background_fill_alpha = .5
    bokeh_objects.append(errors)

    # False Negative Weighting.
    # Intro.
    weighting_intro = f'''
    <p><b>Error types differ in impact</b> - in the case of security incidents, a false negative, 
though possibly rarer than false positives, is likely more costly. For example, downtime suffered 
from a DDoS attack (lost sales/customers) incurs more loss than time wasted chasing a false positive 
(labor hours). </p>

<p>Try playing around with the slider below to see how your thresholding strategy might change 
depending on the relative weight of false negatives to false positives. What does it look like at
10:1, 50:1, etc.?</p>
'''

    weighting_div = Div(text=weighting_intro, width=900, height=100)

    # Now for the weighted errors viz

    default_weighting = 10
    simulations['weighted_FN'] = simulations.FN * default_weighting
    weighted_fn = simulations.weighted_FN
    simulations['total_weighted_error'] = simulations.FP + simulations.weighted_FN
    total_weighted_error = simulations.total_weighted_error
    twe_min = simulations[simulations.total_weighted_error
                          == simulations.total_weighted_error.min()].head(1).squeeze()['multiplier']

    loss_min = ColumnDataSource(data=dict(w=multiplier,
                                          x=false_positives,
                                          y=false_negatives,
                                          z=weighted_fn,
                                          a=total_weighted_error,
                                          b=precision,
                                          c=recall,
                                          d=f1_score
                                          ))

    evaluation = Figure(plot_width=900,
                        plot_height=550,
                        x_range=(multiplier.min(), multiplier.max()),
                        title='Evaluation Metrics vs Weighted Total Error',
                        x_axis_label='Multiplier',
                        y_axis_label='Errors')

    evaluation.title.text_font_size = title_font_size
    evaluation.border_fill_color = cell_bg_color
    evaluation.border_fill_alpha = cell_bg_alpha
    evaluation.background_fill_color = cell_bg_color
    evaluation.background_fill_alpha = plot_bg_alpha
    evaluation.min_border_left = left_border
    evaluation.min_border_right = right_border
    evaluation.min_border_top = top_border
    evaluation.min_border_bottom = bottom_border

    evaluation.line('w', 'a', source=loss_min, line_width=3, line_alpha=0.6,
                    color=total_weighted_color, legend_label='Total Weighted Errors')
    evaluation.yaxis.formatter = NumeralTickFormatter(format='0,0')

    # Evaluation metrics on second right axis.
    evaluation.extra_y_ranges = {"y2": Range1d(start=0, end=1.1)}

    evaluation.add_layout(LinearAxis(y_range_name="y2", axis_label="Score",
                          formatter=NumeralTickFormatter(format='0.00%')), 'right')
    evaluation.line('w', 'b', source=loss_min, line_width=3, line_alpha=0.6,
                    color=precision_color, legend_label='Precision', y_range_name="y2")
    evaluation.line('w', 'c', source=loss_min, line_width=3, line_alpha=0.6,
                    color=recall_color, legend_label='Recall', y_range_name="y2")
    evaluation.line('w', 'd', source=loss_min, line_width=3, line_alpha=0.6,
                    color=f1_color, legend_label='F1 score', y_range_name="y2")
    evaluation.legend.location = "bottom_right"

    slider = Slider(start=1.0, end=1000, value=10, step=.25, title="FN:FP Ratio",
                    bar_color='#FFD100', height=50, margin=(5, 0, 5, 0))

    twe_thresh = Span(location=twe_min, dimension='height', line_color=total_weighted_color,
                      line_dash='dashed', line_width=2)
    twe_label = Label(x=twe_min - .05, y=240, y_units='screen',
                      text=f'TWE Min: {round(twe_min,2)}',
                      text_font_size='10pt', text_font_style='bold',
                      text_align='right', text_color=total_weighted_color)
    evaluation.add_layout(twe_thresh)
    evaluation.add_layout(twe_label)

    # Add in same f1 thresh as previous viz
    evaluation.add_layout(f1_thresh)
    evaluation.add_layout(f1_label)


    handler = CustomJS(args=dict(source=loss_min,
                                 thresh=twe_thresh,
                                 label=twe_label), code="""
       var data = source.data;
       var f = cb_obj.value
       var w = data['w']
       var x = data['x']
       var y = data['y']
       var z = data['z']
       var a = data['a']
       for (var i = 0; i < x.length; i++) {
          z[i] = Math.round(y[i] * f)
          a[i] = z[i] + x[i]
       }
       
       var min_loss = Math.min.apply(null,a)
       var new_thresh = 0
       
       for (var i = 0; i < x.length; i++) {
       if (a[i] == min_loss) {
           new_thresh = w[i]
           thresh.location = new_thresh
           thresh.change.emit()
           label.x = new_thresh
           label.text = `TWE Min: ${new_thresh}`
           label.change.emit()
       }
    }
       source.change.emit();
    """)
    slider.js_on_change('value', handler)

    # Include DataTable of simulation results
    dt_columns = [
        TableColumn(field="w", title="Multiplier"),
        TableColumn(field="x", title="False Positives"),
        TableColumn(field="y", title="False Negatives"),
        TableColumn(field="z", title="Weighted False Negatives"),
        TableColumn(field="a", title="Total Weighted Errors"),
        TableColumn(field="b", title="Precision", formatter=NumberFormatter(format='0.00%')),
        TableColumn(field="c", title="Recall", formatter=NumberFormatter(format='0.00%')),
        TableColumn(field="d", title="F1 Score", formatter=NumberFormatter(format='0.00%')),
    ]

    data_table = DataTable(source=loss_min, columns=dt_columns, width=900, height=400,
                           fit_columns=True, reorderable=True, sortable=True)

    weighting_layout = column([weighting_div, evaluation, slider, data_table], sizing_mode='stretch_width')
    bokeh_objects.append(weighting_layout)

    # Initialize visualizations in browser
    time.sleep(1.5)
    #show(column(bokeh_objects))

    l = grid([
        [bokeh_objects[0]],
        bokeh_objects[1:3],
        bokeh_objects[3:5],
        bokeh_objects[5:7],
        [bokeh_objects[7]]
    ])
    #show(column(bokeh_objects))
    #show(l)
    html = file_html(l, CDN, "CREAM")
    with open("../render.html", "w") as file:
        file.write(html)
    webbrowser.open("file://" + os.path.realpath("../render.html"))

