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

re.compile(r"#![^\n]+")

clusters = Path('scowl-orig.txt').read_text().replace('†','')
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

        except KeyError:
            if clusters.issuperset(map(lambda c: '\n'.join(c), toAdd)):
                skipped += 1
            else:
                stderr.write(f'unable to find cluster>>>\n{cluster}\n<<<skipping hunk\n')
                failed += 1
            
        toRemove = []
        toAdd = []
        curCluster = None
        
    elif curCluster is not None:
        curCluster.append(line)

    else:
        raise ValueError(f'unexpected line: {line}')

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
    
