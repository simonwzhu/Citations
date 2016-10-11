#!/usr/bin/env python3
"""
Create spreadsheets to resolve differences in data entry.
"""
import pandas as pd
import numpy as np

input_file = 'bld/ajps_reference_coding_diff.csv'

resolution_pairs = [('KJK', 'RP'), ('RK', 'TC')]

output_file_prefix = 'data_entry/ajps_reference_coding_diff_resolution'

diff = pd.read_csv(input_file)

for pair in resolution_pairs:
    suffix = '_' + '_'.join(pair)

    reference_columns = ['reference_category_' + x for x in pair]
    left_column = 'reference_category_' + pair[0]
    right_column = 'reference_category_' + pair[1]
    resolution_column = 'reference_category' + suffix + '_resolved'
    conflict_column = 'conflict_ignore_skip' + suffix

    article_columns = ['doi', 'article_ix', 'title']
    match_columns = ['match', 'context']
    output_columns = (article_columns + match_columns + reference_columns +
                      [resolution_column, conflict_column])

    # Two entries conflict if they are non-empty, different, and neither
    # is 'skip'.
    data_entered = diff[reference_columns].notnull()
    conflict = (diff[reference_columns][data_entered].
                replace('skip', value=np.nan).
                apply(pd.Series.nunique, axis=1) > 1)

    left_entry = diff[left_column].notnull()
    right_entry = diff[right_column].notnull()

    left_only = np.all([left_entry, ~right_entry], axis=0)
    right_only = np.all([~left_entry, right_entry], axis=0)

    left_skip = diff[left_column] == 'skip'
    right_skip = diff[right_column] == 'skip'

    agreement = np.equal(diff[left_column], diff[right_column])

    # Resolve automatically as follows:
    # 1. If there is only one entry take that entry.
    # 2. If entries agree, take the left entry.
    # 3. If there are two entries and entries are different, and
    #    one of the entries is 'skip', take 'skip'.
    # Otherwise leave blank for manual resolution.
    take_left = np.any([left_only, agreement,
                        np.all([left_skip, ~right_skip], axis=0)],
                       axis=0)
    take_right = np.any([right_only,
                         np.all([right_skip, ~left_skip], axis=0)],
                        axis=0)

    diff[conflict_column] = conflict
    diff.loc[take_left, resolution_column] = diff.loc[take_left, left_column]
    diff.loc[take_right, resolution_column] = diff.loc[take_right,
                                                       right_column]

    bool_printing = {True: 'True', False: ''}
    diff.replace({conflict_column: bool_printing}, inplace=True)

    diff.to_csv(output_file_prefix + suffix + '.csv',
                columns=output_columns, index=None)
