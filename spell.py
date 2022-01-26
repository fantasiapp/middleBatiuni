import sys
sys.path.append('/var/fantasiapp/batiUni/middle/')
from bdd import DBConnector
sireneConnector = DBConnector('Sirene')

import re
from collections import Counter

def Names():
    return [res[0] for res in sireneConnector.executeRequest('SELECT denominationUniteLegale FROM unites_legales WHERE denominationUniteLegale NOT LIKE ""', True)]

NAMES = Counter(Names())

def P(name, N=sum(NAMES.values())):
    return NAMES[name]/N

def correction(name):
    return max(candidates(name), key=P)

def candidates(name):
    return (known([name]) or known(edits1(name)) or known(edits2(name)) or [name])

def known(names):
    return set(name for name in names if name in NAMES)

def edits1(name):
    characters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890 '
    splits = [(name[:i], name[i:]) for i in range(len(name)+1)]
    deletes = [L + R[1:] for L,R in splits if R]
    transposes = [L + R[1] + R[0] + R[2:] for L,R in splits if len(R)>1]
    replaces = [L + c + R[1:] for L,R in splits if R for c in characters]
    inserts = [L + c + R for L,R in splits for c in characters]
    return set(deletes + transposes + replaces + inserts)

def edits2(name):
    return (e2 for e1 in edits1(name) for e2 in edits1(e1))

if __name__=='__main__':
    #print(NAMES)
    while 1:
        name = input().upper()
        for candidate in candidates(name):
            print(f'{candidate} :, {NAMES[candidate]}')
        print("Best candidate : ", correction(name))
