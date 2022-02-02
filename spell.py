import sys

sys.path.append('/var/fantasiapp/batiUni/middle/')
from bdd import DBConnector
sireneConnector = DBConnector('Sirene')

def Names():
    print("\tLoading enterprise names in RAM")
    return [res[0] for res in sireneConnector.executeRequest('SELECT denominationUniteLegale FROM unites_legales WHERE denominationUniteLegale NOT LIKE ""', True)]

NAMES = Names()

class Corrector:
       
    @classmethod
    def P(cls, name):
        return NAMES[name]

    @classmethod
    def correction(cls, name):
        return max(cls.candidates(name), key=cls.P)

    @classmethod
    def candidates(cls, name):
        return (cls.known([name]) or cls.known(edits1(name)) or cls.known((name)) or [name])

    @classmethod
    def known(cls, names):
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

if __name__=='__main__':
    # corrector = Corrector()
    # while 1:
    #     name = input("Type in a subname :").upper()
    #     for candidate in corrector.candidates(name):
    #         print(f'{candidate} :, {NAMES[candidate]}')
    #     print("Best candidate : ", corrector.correction(name))

    words = ["appeal",
            "executive",
            "snow",
            "theorist",
            "sister",
            "eat",
            "oral",
            "single",
            "pill",
            "reward",
            "enfix",
            "established",
            "allowance",
            "struggle",
            "cultural",
            "overlook",
            "sermon",
            "swarm",
            "fix",
            "rotate",
            "loot",
            "automatic",
            "pillow",
            "roof",
            "ordinary",
            "monopoly",
            "small",
            "closed",
            "expression",
            "restrain",
            "liberty",
            "recognize",
            "concentration",
            "spell",
            "blast",
            "terms",
            "layout",
            "common",
            "thumb",
            "secular",
            "building",
            "attractive",
            "shape",
            "courtship",
            "fee",
            "elephant",
            "protection",
            "stream",
            "palm",
            "wrap"]

    for word in sortByDistance(words, 'stream'):
        print(word, '\t', distance(word, 'stream'))