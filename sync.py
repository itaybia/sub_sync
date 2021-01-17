# Copyright 2021 Itay Bianco
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


import argparse
import bisect
import sys


MAX_DISTANCES = 30
MIN_TIME_BETWEEN_INTERPOLATION_POINTS = 5 * 60 * 1000


def srt_time_to_ms(time_str):
    hours_ms = float(time_str[0:2]) * 3600000
    minutes_ms = float(time_str[3:5]) * 60000
    seconds_ms = float(time_str[6:8]) * 1000
    ms = float(time_str[9:]) + seconds_ms + minutes_ms + hours_ms
    return ms


def ms_to_srt_time(ms):
    hours_ms = ms / 3600000
    ms %= 3600000
    minutes_ms = ms / 60000
    ms %= 60000
    seconds_ms = ms / 1000
    ms %= 1000
    return '%d:%d:%d,%d' % (hours_ms, minutes_ms, seconds_ms, ms)


def parse_srt_file(srt_path, create_entries_list):
    with open(srt_path) as f:
        lines = f.readlines()

    max_distance_times = []
    entries = []
    i = 0
    last_start = 0
    while i < len(lines):
        line = lines[i].strip()
        if not line:
            i += 1
            continue
        index = line
        i += 1
        line = lines[i].strip()
        start, end = line.split(' --> ')
        start = srt_time_to_ms(start)
        end = srt_time_to_ms(end)
        i += 1
        text = []
        line = lines[i].strip()
        while line:
            text.append(line)
            i += 1
            line = lines[i].strip()
        text = '\n'.join(text)

        i += 1
        if 'opensubtitles' in text.lower():
            continue

        if create_entries_list:
            entry = (index, start, end, text)
            entries.append(entry)

        if last_start != 0:
            time_diff_from_prev = start - last_start
            bisect.insort(max_distance_times, (time_diff_from_prev, start))
            if len(max_distance_times) > MAX_DISTANCES:
                max_distance_times = max_distance_times[1:]
        last_start = start

    max_distance_start_times = sorted([x for _, x in max_distance_times])
    print max_distance_times
    print max_distance_start_times
    print [ms_to_srt_time(x) for x in max_distance_start_times]
    return max_distance_start_times, entries


def get_average_score(i, j, arr1, n, m, arr2):
    x0 = arr2[n]
    x1 = arr2[m]

    if x1 - x0 < MIN_TIME_BETWEEN_INTERPOLATION_POINTS:
        return sys.maxint, None, None, None

    y0 = arr1[i]
    y1 = arr1[j]
    a = (y1 - y0) / (x1 - x0)

    min_dist_dict = {}
    for k in xrange(0, len(arr2)):
        x = arr2[k]
        y = y0 + (x - x0) * a
        min_dist = sys.maxint
        min_dist_index = None
        for l in xrange(0, len(arr1)):
            dist = abs(y - arr1[l])
            if dist > 1000:
                continue
            if dist < min_dist:
                min_dist = dist
                min_dist_index = l
        if min_dist_index in min_dist_dict:
            min_dist_dict[min_dist_index] = min(min_dist, min_dist_dict[min_dist_index])
        else:
            min_dist_dict[min_dist_index] = min_dist

    if len(min_dist_dict) < 20:
        return sys.maxint, None, None, None

    sum_dist = 0
    for val in min_dist_dict.itervalues():
        sum_dist += val
    avg = sum_dist / len(min_dist_dict)
    return avg, a, y0, x0


def get_linear_interpolation_params(synced_max_distance_start_times, non_synced_max_distance_start_times):
    min_avg = sys.maxint
    min_avg_indices = None
    min_avg_params = None
    for i in xrange(0, MAX_DISTANCES - 1):
        for j in xrange(i + 1, MAX_DISTANCES):
            for n in xrange(0, MAX_DISTANCES - 1):
                for m in xrange(n + 1, MAX_DISTANCES):
                    avg, a, y0, x0 = get_average_score(i, j, synced_max_distance_start_times, n, m, non_synced_max_distance_start_times)
                    if avg < min_avg:
                        min_avg = avg
                        min_avg_indices = (i, j, n, m)
                        min_avg_params = (a, y0, x0)

    print min_avg_indices
    print [ms_to_srt_time(synced_max_distance_start_times[min_avg_indices[0]]), ms_to_srt_time(synced_max_distance_start_times[min_avg_indices[1]]),
           ms_to_srt_time(non_synced_max_distance_start_times[min_avg_indices[2]]), ms_to_srt_time(non_synced_max_distance_start_times[min_avg_indices[3]])]
    return min_avg_params


def create_output_file(entries_to_sync, linear_interpolation_params_for_sync, output_path):
    a, y0, x0 = linear_interpolation_params_for_sync

    with open(output_path, 'w') as f:
        for entry in entries_to_sync:
            f.write(entry[0])
            f.write('\n')

            start_ms = entry[1]
            modified_start = y0 + (start_ms - x0) * a
            end_ms = entry[2]
            modified_end = y0 + (end_ms - x0) * a
            f.write(ms_to_srt_time(modified_start))
            f.write(' --> ')
            f.write(ms_to_srt_time(modified_end))
            f.write('\n')

            text = entry[3]
            f.write(text)
            f.write('\n\n')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("synced_path", help="display a square of a given number")
    parser.add_argument("non_synced_path", help="display a square of a given number")
    parser.add_argument("output_path", help="display a square of a given number")
    args = parser.parse_args()

    synced_max_distance_start_times, synced_entries = parse_srt_file(args.synced_path, False)
    non_synced_max_distance_start_times, non_synced_entries = parse_srt_file(args.non_synced_path, True)
    interpolation_params = get_linear_interpolation_params(synced_max_distance_start_times, non_synced_max_distance_start_times)
    create_output_file(non_synced_entries, interpolation_params, args.output_path)


if __name__ == "__main__":
    # execute only if run as a script
    main()
