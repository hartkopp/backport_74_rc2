#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0
#
# "Diff of diffs" check for the backports, per function.
#
# For every file, stable branch and top-level C block (function, struct,
# the code between them), compare the difference master <-> branch BEFORE
# the series (finsrc/pre/) with the difference master <-> branch AFTER the
# series (finsrc/). An exact backport leaves this difference unchanged.
#
# Classification of each block:
#   unchanged       same difference before and after (not reported)
#   NEW DIFF        identical before, different after: the backport did
#                   something else than upstream (adaptation or mistake),
#                   the master <-> branch diff of the block is shown
#   aligned         different before, identical after: the series made the
#                   branch identical to master (e.g. prerequisites)
#   DIFF CHANGED    different before and after, but differently: the
#                   diff of diffs of the block is shown
#   only in master / only in branch
#                   block exists on one side only after the series and
#                   did not before
#
# Lines are compared after joining multi-line statements and collapsing
# whitespace, so that pure re-wrapping does not show up.
#
# Usage: scripts/diffdiff.py [finsrc-dir] [--branch X.Y] [--file name]

import argparse
import difflib
import os
import re

MAX_DD = 30
BRANCHES = ['5.10', '5.15', '6.1', '6.6', '6.12', '6.18']
FILES = ['af_can.c', 'bcm.c', 'gw.c', 'isotp.c', 'raw.c', 'can-ml.h',
         'netns-can.h']


def path(d, f, tag):
    base, ext = os.path.splitext(f)
    return os.path.join(d, f'{base}-{tag}{ext}')


def logical_lines(lines):
    """join continuation lines, collapse whitespace"""
    out, cur = [], ''
    for l in lines:
        s = ' '.join(l.split())
        if not s:
            if cur:
                out.append(cur)
                cur = ''
            continue
        if s.startswith(('#', '/*', '*', '//')) and not cur:
            out.append(s)
            continue
        cur = f'{cur} {s}' if cur else s
        if s.endswith((';', '{', '}', ':', '*/', ')')) or s.startswith('#'):
            out.append(cur.replace('( ', '(').replace(' )', ')'))
            cur = ''
    if cur:
        out.append(cur)
    return out


HEAD_RE = re.compile(r'^(?:static\s+|inline\s+|const\s+|struct\s+|enum\s+|'
                     r'union\s+|unsigned\s+|void|int|bool|long|u\d+|size_t|'
                     r'char|[a-z_][a-z0-9_]*\s+\**)')


def blocks(lines):
    """split into top-level blocks: {name: [lines]}"""
    res, order = {}, []
    i, n, glob = 0, len(lines), 0
    cur_glob = []

    def flush_glob():
        nonlocal glob, cur_glob
        if any(x.strip() for x in cur_glob):
            key = f'<toplevel #{glob}>'
            res[key] = cur_glob
            order.append(key)
            glob += 1
        cur_glob = []

    while i < n:
        l = lines[i]
        # a definition starts at column 0 and its body ends with '}' at col 0
        if l and not l[0].isspace() and not l.startswith(('#', '/', '*', '}')) \
                and HEAD_RE.match(l):
            j = i
            while j < n and '{' not in lines[j] and not lines[j].rstrip() \
                    .endswith(';'):
                j += 1
            if j < n and '{' in lines[j] and not lines[j].rstrip().endswith(
                    ('};', ';')) or (j < n and lines[j].rstrip().endswith('{')):
                k = j
                while k < n and not lines[k].startswith('}'):
                    k += 1
                head = ' '.join(x.strip() for x in lines[i:j + 1])
                m = re.search(r'(\w+)\s*\(', head)
                if m and not head.startswith(('struct', 'static struct')) or \
                        (m and '(' in head.split('{')[0] and '=' not in head):
                    name = m.group(1) + '()'
                else:
                    m2 = re.search(r'((?:struct|enum|union)\s+\w+|\w+)\s*(=\s*)?\{',
                                   head)
                    name = m2.group(1) if m2 else head[:40]
                flush_glob()
                key = name
                while key in res:
                    key += "'"
                res[key] = lines[i:k + 1]
                order.append(key)
                i = k + 1
                continue
        cur_glob.append(l)
        i += 1
    flush_glob()
    return res, order


def ldiff(a, b):
    return [l for l in difflib.unified_diff(a, b, lineterm='', n=0)
            if not l.startswith(('---', '+++', '@@'))]


def read(p):
    with open(p) as fh:
        return fh.read().splitlines()


def by_name(lines):
    b, order = blocks(lines)
    return {k: logical_lines(v) for k, v in b.items()}, order


def merge_locked(x, y):
    """When foo_locked() exists in x but not in y, compare x's foo() and
    foo_locked() together against y's foo() (e.g. raw_setsockopt_locked()
    split upstream that older trees do not have)."""
    for nm in [k for k in x if k.endswith('_locked()')]:
        base = nm[:-len('_locked()')] + '()'
        if nm not in y and base in x and base in y:
            x[base] = x.pop(nm) + x[base]
            x[base + ' (+ _locked)'] = x.pop(base)
            y[base + ' (+ _locked)'] = y.pop(base)


def fmt(dd):
    """render diff-of-diff lines: 1st char before(-)/after(+),
    2nd char master-only(-)/branch-only(+)"""
    out = []
    for l in dd:
        when = 'before' if l[0] == '-' else 'after '
        who = 'master' if l[1] == '-' else 'branch'
        out.append(f'{when} {who}: {l[2:]}')
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('dir', nargs='?',
                    default=os.path.join(os.path.dirname(__file__), '..',
                                         'finsrc'))
    ap.add_argument('--branch', action='append')
    ap.add_argument('--file', action='append')
    a = ap.parse_args()
    pre = os.path.join(a.dir, 'pre')
    total = 0
    for br in a.branch or BRANCHES:
        tag = br.replace('.', '')
        print(f'=== linux-{br}.y')
        for f in a.file or FILES:
            mp, _ = by_name(read(path(pre, f, 'master')))
            bp, _ = by_name(read(path(pre, f, tag)))
            ma, order = by_name(read(path(a.dir, f, 'master')))
            ba, border = by_name(read(path(a.dir, f, tag)))
            merge_locked(mp, bp)
            merge_locked(bp, mp)
            merge_locked(ma, ba)
            merge_locked(ba, ma)
            order = [k for k in order if k in ma] + \
                [k for k in ma if k not in order]
            names = order + [x for x in ba if x not in order]
            report = []
            for nm in names:
                if nm.startswith('<toplevel'):
                    continue
                m0, b0, m1, b1 = (mp.get(nm), bp.get(nm), ma.get(nm),
                                  ba.get(nm))
                if m1 is None or b1 is None:
                    if (m0 is None) != (b0 is None) and \
                            (m0 is None) == (m1 is None):
                        continue  # one-sided before and after
                    side = 'branch' if m1 is None else 'master'
                    if m1 is None and b1 is None:
                        continue
                    report.append((nm, f'only in {side}', []))
                    continue
                d0 = ldiff(m0 or [], b0 or [])
                d1 = ldiff(m1, b1)
                if d0 == d1:
                    continue
                if not d0:
                    report.append((nm, 'NEW DIFF',
                                   [f'after  {"master" if l[0] == "-" else "branch"}: {l[1:]}'
                                    for l in d1]))
                elif not d1:
                    report.append((nm, 'aligned', []))
                else:
                    dd = [l for l in difflib.unified_diff(d0, d1, lineterm='',
                                                          n=0)
                          if not l.startswith(('---', '+++', '@@'))]
                    if len(dd) <= MAX_DD:
                        report.append((nm, 'DIFF CHANGED', fmt(dd)))
                        continue
                    # block restructured upstream: show both changes
                    up = ldiff(m0 or [], m1)
                    bc = ldiff(b0 or [], b1)
                    lines = [f'upstream change ({len(up)} lines, not shown)'
                             if len(up) > MAX_DD else 'upstream change:']
                    if len(up) <= MAX_DD:
                        lines += ['  ' + l for l in up]
                    lines += ['backport change:'] + ['  ' + l for l in bc]
                    report.append((nm, 'DIFF CHANGED (restructured upstream, '
                                   'compare the changes)', lines))
            if not report:
                print(f'  {f}: identical to upstream')
                continue
            print(f'  {f}:')
            for nm, kind, lines in report:
                print(f'    {nm}: {kind}')
                for l in lines:
                    print(f'        {l}')
                total += 1
        print()
    print(f'{total} block(s) to review')


if __name__ == '__main__':
    main()
