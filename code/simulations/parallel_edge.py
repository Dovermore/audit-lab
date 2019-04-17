from multiprocessing import Process, Pool, pool
from simulations.irvedge import irv_edge
from datetime import datetime
from os import path
import os
from csv_readers import read_csv_file
from collections import defaultdict as dd
from utils import greatest_name
import sys
import csv


def simulate(n, election_name="irv-", spec_dir="2-edge"):
    time_stamp = datetime.now().strftime("%m%d%Y%H%M%S")
    prefix = time_stamp + election_name
    pre_format = time_stamp + "{0}{1:0%d}" % (len(str(n)))
    names = [pre_format.format(election_name, i) for i in range(n)]
    spec_dirs = [spec_dir] * n
    arg_pairs = list(zip(names, spec_dirs))
    with Pool(n) as p:
        p.starmap(irv_edge, arg_pairs)
        p.close()
        p.join()
    print("fin")
    return prefix


def counting(prefix, dirpath="./elections"):
    results = dd(int)
    output_prefix = "audit-output-contest-status"
    output_postfix = ".csv"
    output_inner_dir = path.join("3-audit", "34-audit-output")

    output_fields = ["Measurement id", "Contest", "Risk Measurement Method",
                     "Risk Limit", "Risk Upset Threshold", "Sampling Mode",
                     "Status", "Param 1", "Param 2"]

    for election_dir in os.listdir(dirpath):
        # Find the correct directory
        if election_dir.startswith(prefix):
            election_dir = path.join(dirpath, election_dir)
            output_dir = path.join(election_dir, output_inner_dir)
            if path.exists(output_dir):
                file = greatest_name(output_dir, output_prefix, output_postfix)
                file = path.join(output_dir, file)
                field_dict = read_csv_file(file, required_fieldnames
                                           =output_fields)
                print(file)
                print(field_dict)
                for row in field_dict:
                    results[row["Status"]] += 1

    result_path = path.join(".", "results")
    if not path.exists(result_path):
        os.makedirs(result_path)

    all_status = ["Upset", "Passed", "Open"]
    result_csv = path.join(result_path, prefix+".csv")
    try:
        with open(result_csv, 'w') as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=all_status)
            writer.writeheader()
            for data in [results, ]:
                writer.writerow(data)
    except IOError:
        print("I/O error")
    return results


if __name__ == "__main__":
    if len(sys.argv) > 1:
        n = int(sys.argv[1])
        election_name = sys.argv[2]
        spec_dir = sys.argv[3]
        prefix = simulate(n, election_name, spec_dir)
    else:
        n = 2
        prefix = simulate(n)

    print(counting(prefix))
