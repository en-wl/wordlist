#!/usr/bin/python3

import time
import os
import shutil
import io
import sys
import re

from sys import stdout, stderr
from pathlib import Path
from collections import deque

if len(sys.argv) > 1 and sys.argv[1] == '--prune':
    prune = True
elif len(sys.argv) > 1:
    sys.stderr.write(f"usage {sys.argv[0]} [--prune] < PATCHFILE > RESULT\n")
    exit(1)
else:
    prune = False

clusters = Path('scowl-new.txt').read_text().replace('†','')
clusters = re.sub(r" +#![^\n]+", "", clusters)
clusters = clusters.split('\n\n')
clusters.pop()
clusters = set(clusters)
newClusters = set()

patchLines = sys.stdin.read().replace('†','')
patchLines = re.sub(r" +#![^\n]+", "", patchLines)
patchLines = deque(patchLines.split('\n'))

total = 0
skipped = 0
failed = 0

toRemove = []
toAdd = []
curCluster = None
good = []
bad = []
while True:
    try:
        line = patchLines.popleft()
    except IndexError:
        break

    if line == '' and curCluster is None:
        pass

    elif line == '---':
        curCluster = []
        toRemove.append(curCluster)

    elif line == '+++':
        curCluster = []
        toAdd.append(curCluster)

    elif line == '===':
        try:
            if toRemove:
                total += 1
                for cluster in toRemove:
                    cluster = '\n'.join(cluster)
                    clusters.remove(cluster)
                for cluster in toAdd:
                    cluster = '\n'.join(cluster)
                    newClusters.add(cluster)
            else:
                for cluster in toAdd:
                    total += 1
                    cluster = '\n'.join(cluster)
                    if cluster in clusters:
                        skipped += 1
                        continue
                    newClusters.add(cluster)
            good.append((toRemove,toAdd))

        except KeyError:
            if clusters.issuperset('\n'.join(c) for c in toAdd):
                skipped += 1
            else:
                stderr.write(f'unable to find cluster>>>\n{cluster}\n<<<skipping hunk\n')
                failed += 1
            bad.append((toRemove,toAdd))

        toRemove = []
        toAdd = []
        curCluster = None

    elif curCluster is not None:
        curCluster.append(line)

    else:
        raise ValueError(f'unexpected line: {line}')

if prune:

    for toRemove,toAdd in good:
        for cluster in toRemove:
            print('---')
            for line in cluster:
                print(line)
        for cluster in toAdd:
            print('+++')
            for line in cluster:
                print(line)
        print('===')
        print()

else:

    for cluster in newClusters:
        stdout.write(cluster)
        stdout.write('\n\n')

    stdout.write('\n')

    for cluster in clusters:
        stdout.write(cluster)
        stdout.write('\n\n')


    if skipped > 0:
        stderr.write(f'skipped {skipped}/{total} hunks\n')

    if failed > 0:
        stderr.write(f'{failed}/{total} hunks failed\n')
        exit(1)

