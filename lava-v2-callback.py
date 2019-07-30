#!/usr/bin/env python3

# Copyright (C) 2018, 2019 Collabora Limited
# Author: Guillaume Tucker <guillaume.tucker@collabora.com>
#
# This module is free software; you can redistribute it and/or modify it under
# the terms of the GNU Lesser General Public License as published by the Free
# Software Foundation; either version 2.1 of the License, or (at your option)
# any later version.
#
# This library is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU Lesser General Public License for more
# details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this library; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA

import argparse
import json
import sys
import yaml

# copied from lava-server/lava_scheduler_app/models.py
SUBMITTED = 0
RUNNING = 1
COMPLETE = 2
INCOMPLETE = 3
CANCELED = 4
CANCELING = 5

# git bisect return codes
BISECT_PASS = 0
BISECT_SKIP = 1
BISECT_FAIL = 2

# LAVA job result names
LAVA_JOB_RESULT_NAMES = {
    COMPLETE: "PASS",
    INCOMPLETE: "FAIL",
    CANCELED: "UNKNOWN",
    CANCELING: "UNKNOWN",
}

# git bisect and LAVA job status map
BOOT_STATUS_MAP = {
    COMPLETE: BISECT_PASS,
    INCOMPLETE: BISECT_FAIL,
}

TEST_CASE_STATUS_MAP = {
    'pass': BISECT_PASS,
    'skip': BISECT_SKIP,
    'fail': BISECT_FAIL,
}


def is_infra_error(cb):
    lava_yaml = cb['results']['lava']
    lava = yaml.load(lava_yaml)
    stages = {s['name']: s for s in lava}
    job_meta = stages['job']['metadata']
    return job_meta.get('error_type') == "Infrastructure"


def handle_boot(cb):
    job_status = cb['status']
    print("Status: {}".format(LAVA_JOB_RESULT_NAMES[job_status]))
    return BOOT_STATUS_MAP.get(job_status, BISECT_SKIP)


def handle_test(cb, full_case_name):
    name_split = full_case_name.split('.')
    test_name = name_split.pop()
    test_suite = name_split.pop()
    # ToDo: handle test sets
    if name_split:
        raise Exception("Test sets not supported yet...")
        test_set = test_suite
        test_suite = name_split.pop()
    else:
        test_set = None

    print("suite: {}, set: {}, test: {}".format(
        test_suite, test_set, test_name))

    results = cb['results']
    for name, test_results_yaml in results.items():
        if name == 'lava':
            # ToDo: handle login test case (reuse backend code...)
            continue
        name = name.partition("_")[2]
        if name == test_suite:
            test_results = yaml.load(test_results_yaml)
            for test_case in test_results:
                if test_case['name'] == test_name:
                    test_case_result = test_case['result']
                    print("Test case result: {}".format(test_case_result))
                    return TEST_CASE_STATUS_MAP[test_case_result]

    print("Warning: failed to find test case result")
    return BISECT_SKIP


def main(args):
    with open(args.json) as json_file:
        cb = json.load(json_file)

    if args.token and cb['token'] != args.token:
        print("Token mismatch")
        sys.exit(1)

    if is_infra_error(cb):
        print("Infrastructure error")
        ret = BISECT_SKIP
    elif args.case:
        ret = handle_test(cb, args.case)
    else:
        ret = handle_boot(cb)

    sys.exit(ret)


if __name__ == '__main__':
    parser = argparse.ArgumentParser("Parse LAVA v2 callback data")
    parser.add_argument("json",
                        help="Path to the JSON data file")
    parser.add_argument("--token",
                        help="Secret authorization token")
    parser.add_argument("--case",
                        help="Test case name in dotted syntax")
    args = parser.parse_args()
    main(args)
