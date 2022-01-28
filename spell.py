import sys
sys.path.append('/var/fantasiapp/batiUni/middle/')
from bdd import DBConnector
sireneConnector = DBConnector('Sirene')

import re
from collections import Counter

class Corrector:
    NAMES = None

    def __init__(self):
        if not Corrector.NAMES:
            Corrector.NAMES = Counter(self.Names())

    def Names(self):
        return [res[0] for res in sireneConnector.executeRequest('SELECT denominationUniteLegale FROM unites_legales WHERE denominationUniteLegale NOT LIKE ""', True)]

    def P(self, name):
        return Corrector.NAMES[name]

    def correction(self, name):
        return max(self.candidates(name), key=self.P)

    def candidates(self, name):
        return (self.known([name]) or self.known(Corrector.edits1(name)) or self.known(Corrector.edits2(name)) or [name])

    def known(self, names):
        return set(name for name in names if name in Corrector.NAMES)

    @classmethod
    def edits1(cls, name):
        characters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890 '
        splits = [(name[:i], name[i:]) for i in range(len(name)+1)]
        deletes = [L + R[1:] for L,R in splits if R]
        transposes = [L + R[1] + R[0] + R[2:] for L,R in splits if len(R)>1]
        replaces = [L + c + R[1:] for L,R in splits if R for c in characters]
        inserts = [L + c + R for L,R in splits for c in characters]
        return set(deletes + transposes + replaces + inserts)

    @classmethod
    def edits2(cls, name):
        return (e2 for e1 in cls.edits1(name) for e2 in cls.edits1(e1))

if __name__=='__main__':
    corrector = Corrector()
    while 1:
        name = input().upper()
        for candidate in corrector.candidates(name):
            print(f'{candidate} :, {Corrector.NAMES[candidate]}')
        print("Best candidate : ", corrector.correction(name))
