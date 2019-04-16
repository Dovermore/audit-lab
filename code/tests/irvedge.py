""" test-4-easy.py
    test for synthesizing (wtth syn2.py) and running audit on election '4-easy'.
"""

import sys
sys.path.append("../..")

import cli_syn
import cli_OpenAuditTool
import OpenAuditTool
import warnings
from datetime import datetime


class Args(object):
    """ Class subclassed from object so we can hang attributes off of it.
    """
    pass

def irv_edge(name):
    """ Generate election 8-irv1 using syn2 then run audit on it with OpenAuditTool.
    """
    with warnings.catch_warnings(record=True):
        # Generate election from object storing pseudo command-line arguments.
        e = OpenAuditTool.Election()
        syn_args = Args()
        syn_args.election_dirname = name
        syn_args.syn_type = '3'
        cli_syn.dispatch(e, syn_args)

        # Audit election
        e = OpenAuditTool.Election()
        OpenAuditTool_args = Args()
        OpenAuditTool_args.election_dirname = name
        OpenAuditTool_args.election_name = name
        OpenAuditTool_args.elections_root = './elections'
        OpenAuditTool_args.set_audit_seed = datetime.now().second
        OpenAuditTool_args.read_election_spec = False
        OpenAuditTool_args.read_reported = False
        OpenAuditTool_args.make_audit_orders = False
        OpenAuditTool_args.read_audited = False
        OpenAuditTool_args.audit = True
        OpenAuditTool_args.pause = False

        # added for new planner code:
        OpenAuditTool_args.num_winners = 1
        OpenAuditTool_args.max_num_it = 100
        OpenAuditTool_args.sample_by_size = False
        OpenAuditTool_args.use_discrete_rm = False
        OpenAuditTool_args.pick_county_func = "round_robin"
        cli_OpenAuditTool.dispatch(e, OpenAuditTool_args)
