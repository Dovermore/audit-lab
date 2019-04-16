# outcomes.py
# Ronald L. Rivest (with Karim Husayn Karimi)
# July 7, 2017
# python3

"""
Tally and outcome computations.
Code to compute an election outcome, given a sequence of votes and a contest type.
Also known as "social choice functions".

An outcome is always a *tuple* of ids, even if there is only one winner.
"""

# TBD: Tie-breaking, etc.


import ids
import rcv


def compute_tally(vec):
    """
    Here vec is an iterable of hashable elements.
    Return dict giving tally of elements.
    """

    tally = {}
    for x in vec:
        tally[x] = tally.get(x, 0) + 1
    return tally


def plurality(e, cid, tally):
    """
    Return, for input dict tally mapping votes to (int) counts, 
    vote with largest count.  (Tie-breaking done arbitrarily here.)
    Winning vote must be a valid winner 
    (e.g. not ("-Invalid",) or ("-NoSuchContest",) )
    an Exception is raised if this is not possible.
    An undervote or an overvote can't win.
    """
    max_cnt = -1e90
    max_vote = None
    for vote in tally:
        if tally[vote] > max_cnt and \
           len(vote) == 1 and \
           not ids.is_error_selid(vote[0]):
            max_cnt = tally[vote]
            max_vote = vote

    if max_vote==None:
        assert "No winner allowed in plurality contest.", tally
    return max_vote


def approval(e, cid, tally):
    """
    {("Alice","Bob"):3,("Alice"):2,("Eve"):1,():4}
    """
    approval_tally = {}
    for accepted_candidates in tally.keys():
        count = tally[accepted_candidates]
        for candidate in accepted_candidates:
            if candidate in approval_tally.keys():
                approval_tally[candidate] = approval_tally[candidate] + count
            else:
                approval_tally[candidate] = count
    fixed_approval_tally = {(k,): approval_tally[k] for k in approval_tally.keys()}
    outcome = plurality(e,cid,fixed_approval_tally)
    return outcome


def IRV(e, cid, tally):
    """
    Handling basic IRV voting.
    :param e: Election object
    :param cid: contest id
    :param tally: The tally of ballots
    :return: (winner, )
    """
    # For preferential voting, the tally should be:
    # {("1-a", "3-b", "2-c"): count ... }
    # Preprocess the format to the required format for rcv.py
    # {("a", "c", "b"): count ... }

    ordered_tally = {}
    for vote in tally:
        ordered_vote: str = sorted(vote)
        ordered_candidates = []
        for rank_candidate in ordered_vote:
            next_rank, candidate = rank_candidate.split("-")
            ordered_candidates.append(candidate)
        ordered_candidates = tuple(ordered_candidates)
        ordered_tally[ordered_candidates] = tally[vote]
    tie_breaker = []
    # return rcv.rcv_winner(ordered_tally, tie_breaker, False)
    return rcv.rcv_winner(ordered_tally, tie_breaker, False),


def compute_ro_c(e):
    """ 
    Compute reported outcomes ro_c for each cid, from e.rn_cr. 
    """

    e.ro_c = dict()
    for cid in e.rn_cr:
        tally = e.rn_cr[cid]
        e.ro_c[cid] = compute_outcome(e, cid, tally)


def compute_outcome(e, cid, tally):
    """
    Return outcome for the given contest, given tally of votes.
    """

    if e.contest_type_c[cid].lower()=="plurality":
        return plurality(e, cid, tally)
    elif e.contest_type_c[cid].lower()=="approval":
        return approval(e, cid, tally)
    elif e.contest_type_c[cid].lower()=="irv":
        return IRV(e, cid, tally)
    else:
        # TBD: IRV, etc...
        raise NotImplementedError(("Non-plurality outcome rule {} for contest {}"
                                   "not yet implemented!")
                                   .format(e.contest_type_c[cid], cid))


def compute_tally2(vec):
    """
    Input vec is an iterable of (a, r) pairs. 
    (i.e., (actual vote, reported vote) pairs).
    Return dict giving mapping from rv to dict
    giving tally of av's that appear with that rv.
    (Used for comparison audits.)
    """

    tally2 = {}
    for (av, rv) in vec:
        if rv not in tally2:
            tally2[rv] = compute_tally([aa for (aa, rr)
                                        in vec if rv == rr])
    return tally2




