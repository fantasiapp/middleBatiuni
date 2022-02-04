import sys

sys.path.append('/var/fantasiapp/batiUni/middle/')
from bdd import DBConnector
sireneConnector = DBConnector('Sirene')

from collections import Counter
from itertools import chain

def Names():
    print("\tLoading enterprise names in RAM")
    return [res[0] for res in sireneConnector.executeRequest('SELECT denominationUniteLegale FROM unites_legales WHERE denominationUniteLegale NOT LIKE ""', True)]

NAMES = Names()
NAMESCOUNTER = Counter(NAMES)

class Corrector:
       
    @classmethod
    def P(cls, name):
        return NAMESCOUNTER[name]

    @classmethod
    def correction(cls, name, maxDistance: int=2):
        return max(cls.candidates(name, maxDistance), key=cls.P)

    @classmethod
    def candidates(cls, name, maxDistance: int=2):
        if maxDistance==2:
            return (cls.known([name]) or cls.known(edits1(name)) or cls.known(edits2(name)) or [name])

    @classmethod
    def known(cls, names):
        return set(name for name in names if name in NAMESCOUNTER)

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

def editsRecursive(name, depth):
    print("editsRecursive for", name, "with depth", depth)
    if depth==0:
        return (name)
    else:
        ans = ()
        for closeName in edits1(name):
            ans = chain(ans, editsRecursive(closeName, depth-1))
        return ans

def distance(a: str, b: str):
    D = [[0 for j in range(len(b)+1)] for i in range(len(a)+1)]
    i = 0
    j = 0
    cost = 0

    for i in range(len(a)+1):
        D[i][0] = i
    for j in range(len(b)+1):
        D[0][j] = j
    
    for i in range(1, len(a)+1):
        for j in range(1, len(b)+1):
            cost = a[i-1]!=b[j-1]
            D[i][j] = min(min(D[i-1][j]+1, D[i][j-1]+1), D[i-1][j-1]+cost)
    
    return D[len(a)][len(b)]

def sortByDistance(words: list, word: str):
    def distanceWithWord(b: str):
        return distance(word, b)

    words.sort(key=distanceWithWord)
    return words
