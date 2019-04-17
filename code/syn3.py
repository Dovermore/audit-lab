# syn3.py
# Ronald L. Rivest
# August 5, 2017 (rev. Sep. 22, 2017)
# python3

"""
Routines to generate synthetic elections of "type 3".
Called from syn.py.
In support of OpenAuditTool.py audit support program.
"""

import copy
import logging
import numpy as np

import OpenAuditTool
import csv_readers
import audit_orders
import utils
import csv_writers
import csv

import os
from os import path

import time

# logging.basicConfig(level=logging.INFO)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
DEBUG = True


def process_spec(e, synpar, meta, actual, reported):
    """
    Initialize Election e according to spec in list L.

    Here e is of type OpenAuditTool.Election

    Here synpar is of type syn.Syn_Parameters

    Each item in L has the form:
        (cid, pbcid, rv, av, num)
    where
        cid = contest id
        pbcid = paper ballot collection id
        rv = reported vote
             (may be ("-noCVR",) if pbcid is noCVR type
        av = actual vote
        num = number of ballots of this type
    Either or both of rv and av may be
        ("-NoSuchContest",)
        ("-Invalid",)
        or other such votes with selection ids starting with "-",
        signifying that they can't win the contest.
    The votes rv and av are arbitrary tuples, and may contain
    0, 1, 2, or more selection ids.

    The FIRST av for a given contest becomes the "reported winner"
    for that contest, even if "num" is zero for that row or if the
    reported or actual votes don't show that vote as the "winner".
    """

    # Store the election meta data
    for cid, pbcid, ro_c, audit_rate, contestants in meta:
        logger.info("Meta:    %s %s %s %s", cid, pbcid, ro_c, audit_rate)

        # Record contest
        if cid not in e.cids:
            e.cids.append(cid)
            e.contest_type_c[cid] = "irv"
            e.params_c[cid] = ""
            e.write_ins_c[cid] = "no"
            e.selids_c[cid] = {}
            e.ro_c[cid] = ro_c      # first av becomes reported outcome
            mid = "M{}-{}".format(len(e.cids), cid)
            e.mids.append(mid)
            e.cid_m[mid] = cid
            e.risk_method_m[mid] = "Bayes"
            e.risk_limit_m[mid] = 0.025
            e.risk_upset_m[mid] = 0.975
            e.sampling_mode_m[mid] = "Active"
            e.initial_status_m[mid] = "Open"
            e.risk_measurement_parameters_m[mid] = ("", "")

        # Record collection identifiers
        if pbcid not in e.pbcids:
            e.pbcids.append(pbcid)
            e.manager_p[pbcid] = "Nobody"
            e.cvr_type_p[pbcid] = "CVR"
            e.required_gid_p[pbcid] = ""
            e.possible_gid_p[pbcid] = ""
            e.bids_p[pbcid] = []
            e.boxid_pb[pbcid] = {}
            e.position_pb[pbcid] = {}
            e.stamp_pb[pbcid] = {}
            e.max_audit_rate_p[pbcid] = int(audit_rate)
            e.comments_pb[pbcid] = {}

        # Add all combinations of selections to the selection pool
        for contestant in contestants:
            selids = [str(i)+"-"+contestant for i
                      in range(1, len(contestants)+1)]
            for selid in selids:
                if selid not in e.selids_c[cid]:
                    e.selids_c[cid][selid] = True

    for (cid, pbcid, num, av) in actual:
        logger.info("actual    %s %s %s %s", cid, pbcid, av, num)

        # When a row is not given specifying contest and winner
        # record the selection id for that vote
        # for selid in av:
        #     if selid not in e.selids_c[cid]:
        #         e.selids_c[cid][selid] = True

        # Record votes
        for pos in range(1, int(num)+1):
            bid = "bid{}".format(1+len(e.bids_p[pbcid]))
            utils.nested_set(e.av_cpb, [cid, pbcid, bid], av)
            e.bids_p[pbcid].append(bid)
            e.boxid_pb[pbcid][bid] = "box1"
            e.position_pb[pbcid][bid] = pos
            e.stamp_pb[pbcid][bid] = ""
            e.comments_pb[pbcid][bid] = ""

    # Start the counter for reported vote from 1
    rv_map = {pbcid: 1 for pbcid in e.bids_p}
    # Update reported votes
    for (cid, pbcid, num, rv) in reported:
        logger.info("actual    %s %s %s %s", cid, pbcid, rv, num)

        # When a row is not given specifying contest and winner
        # record the selection id for that vote
        for selid in rv:
            if selid not in e.selids_c[cid]:
                e.selids_c[cid][selid] = True

        for pos in range(1, int(num)+1):
            bid = "bid{}".format(rv_map[pbcid])
            rv_map[pbcid] += 1
            utils.nested_set(e.rv_cpb, [cid, pbcid, bid], rv)

    # The number of reported vote should be the same as actual vote
    assert all([len(e.bids_p[pbcid]) == rv_map[pbcid] - 1 for
                pbcid in e.bids_p])


def shuffle_votes(e, synpar):

    # shuffle rv, av lists
    for cid in e.rv_cpb:
        for pbcid in e.rv_cpb[cid]:
            # sorted need in following line for reproducible results
            bids = [bid for bid in sorted(e.rv_cpb[cid][pbcid])]
            L = [(e.rv_cpb[cid][pbcid][bid],
                  e.av_cpb[cid][pbcid][bid])
                 for bid in bids]
            synpar.RandomState.shuffle(L)           # in-place
            for i in range(len(bids)):
                bid = bids[i]
                (rv, av) = L[i]
                e.rv_cpb[cid][pbcid][bid] = rv
                e.av_cpb[cid][pbcid][bid] = av
            if DEBUG:
                debug_path = path.join(".", "debug")
                if not path.exists(debug_path):
                    os.makedirs(debug_path)
                    debug_filepath = path.join(debug_path,
                                               e.election_name+".csv")
                    with csv.writer(open(debug_filepath)) as csv_writer:
                        for pair in L:
                            csv_writer.writerow(pair)

##############################################################################
##

def read_meta_csv(e, synpar):
    """
    Read file defining syn3 synthetic election spec.
    """
    syn3_pathname = os.path.join(OpenAuditTool.ELECTIONS_ROOT,
                                 "syn3_specs", synpar.election_dirname)
    try:
        # Use config dir if properly defined
        if synpar.config_dirname is not None:
            syn3_pathname = os.path.join(OpenAuditTool.ELECTIONS_ROOT,
                                         "syn3_specs", synpar.config_dirname)
    except NameError:
        pass
    filename = utils.greatest_name(syn3_pathname,
                                   "meta",
                                   ".csv")
    file_pathname = os.path.join(syn3_pathname, filename)
    fieldnames = ["Contest",
                  "Collection",
                  "Winner",
                  "Audit Rate",
                  "Contestants"
                  ]
    rows = csv_readers.read_csv_file(file_pathname,
                                     fieldnames,
                                     varlen=True)
    return [(row["Contest"],
             row["Collection"],
             (row["Winner"], ),
             row["Audit Rate"],
             row["Contestants"])
            for row in rows]


def read_vote_csv(e, synpar, reported=False):
    """
    Read file defining syn3 synthetic election spec.
    """

    syn3_pathname = os.path.join(OpenAuditTool.ELECTIONS_ROOT,
                                 "syn3_specs", synpar.election_dirname)
    try:
        # Use config dir if properly defined
        if synpar.config_dirname is not None:
            syn3_pathname = os.path.join(OpenAuditTool.ELECTIONS_ROOT,
                                         "syn3_specs", synpar.config_dirname)
    except NameError:
        pass

    filename = utils.greatest_name(syn3_pathname,
                                   "reported" if reported else "actual",
                                   ".csv")
    file_pathname = os.path.join(syn3_pathname, filename)
    fieldnames = ["Contest",
                  "Collection",
                  "Number",
                  "Votes"
                  ]
    rows = csv_readers.read_csv_file(file_pathname,
                                     fieldnames,
                                     varlen=True)
    return [(row["Contest"],
             row["Collection"],
             row["Number"],
             row["Votes"])
            for row in rows]


def generate_syn_type_3(e, args):

    synpar = copy.copy(args)
    meta_rows = read_meta_csv(e, synpar)
    actual_rows = read_vote_csv(e, synpar, False)
    reported_rows = read_vote_csv(e, synpar, True)
    process_spec(e, synpar, meta_rows, actual_rows, reported_rows)
    e.audit_seed = int(time.clock() * 100000)
    synpar.RandomState = np.random.RandomState(e.audit_seed)
    # synpar.RandomState = np.random.RandomState()
    print(f"seed for RandomState: {e.audit_seed}")
    shuffle_votes(e, synpar)
    audit_orders.compute_audit_orders(e)

    debug = False
    if debug:
        for key in sorted(vars(e)):
            logger.info(key)
            logger.info("    ", vars(e)[key])

    csv_writers.write_csv(e)
