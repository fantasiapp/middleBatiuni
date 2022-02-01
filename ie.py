from pdfExtraction import *
import re
import spell
import requests

from bdd import DBConnector

version = os.path.dirname(__file__).split('/')[-1]
if version in ['temp', 'work', 'distrib', 'current']:
    batiuniConnector = DBConnector('batiUni'+version.capitalize())
else:
    batiuniConnector = DBConnector('batiUniWork')

###############
# Definitions #
###############

# Classes

class Block:
    '''
        Blocks of words in the layout
        Used as nodes of a tree, with children
    '''

    def __init__(self, id, line, words) -> None:
        self.id = id
        self.words = words
        self.fontColor = randomColor()
        self.children = []
        self.line = line

    def isLeaf(self)->bool:
        return (not self.children)


class Split:
    def __init__(self, criteria: float, block1: list, block2: list, vertical: bool, line: tuple):
        self.criteria, self.block1, self.block2, self.vertical, self.line = criteria, block1, block2, vertical, line 

    def __gt__(self, other):
        return self.criteria > other.criteria


def regex2Approximation(s: str) -> list[str]:
    '''
        Given a string, this function generates close regex
    '''
    return ("".join(s[k] if k!=i and k!=j else '.' for k in range(len(s))) for i in range(len(s)) for j in range(i+1, len(s)))

class Extractor:

    def __init__(self, path: str):
        '''
            Text pre-processing;
            Should it be uppercased ?
        '''
        self.path = path
        text = extractFullTextWithOCR(path)
        text = ' '.join(text.split('\n'))
        while '  ' in text:
            text = text.replace('  ', ' ')
        self.text = text
        # print(text)

    def regexSearch(self, pattern, groups: list[tuple], header: str=""):
        if header:
            #On doit chercher ici si un endroit du texte ressemble à 
            pattern2 = header + '\s.*?' + pattern
            m = re.search(pattern2, self.text)
            if m:
                return {field: m.group(groupIndex) if m else None for (field, groupIndex) in groups}
            for neighbor in spell.edits1(header):
                pattern2 = neighbor + '\s.*?' + pattern
                m = re.search(pattern2, self.text)
                if m:
                    return {field: m.group(groupIndex) if m else None for (field, groupIndex) in groups}
        m = re.search(pattern, self.text)
        # print("Search with pattern", pattern, "found", m.group(groups[0][1]) if m else None)
        return {field: m.group(groupIndex) if m else None for (field, groupIndex) in groups}

    def getValidityPeriod(self):
        pattern = r'du(\d\d\/\d\d\/\d\d\d\d)\s.*?au\s.*?(\d\d\/\d\d\/\d\d\d\d)'
        return self.regexSearch(pattern, [('validityBegin', 1), ('validityEnd', 2)])

    def getValidityEnd(self):
        pattern = r'[Vv][Aa][Ll](([Aa][Bb][Ll][Ee])|([Ii][Dd][Ii][Tt][ÉéEe]))\s.*?(\d\d\/\d\d\/\d\d\d\d)'
        return self.regexSearch(pattern, [('validityEnd', 4)])

    def getEmailAdress(self):
        pattern = r'\S+\@\S+.(fr|com|net|org)'
        return self.regexSearch(pattern, [('emailAdress', 0)])

    def getPhoneNumber(self):
        pattern = r'\D\s((\d\d)([\.\- ]?))((\d\d)([\.\- ]?))((\d\d)([\.\- ]?))((\d\d)([\.\- ]?))((\d\d)([\.\- ]?))\D'
        m = re.search(pattern, self.text)
        return {
            'phoneNumber': m.group(2)+m.group(5)+m.group(8)+m.group(11)+m.group(14) if m else None
        }

    def getSiren(self):
        pattern = r'[Ss][Ii][Rr][Ee][Nn].+?([\d ]{9})\s'
        return self.regexSearch(pattern, [('siren', 1)])

    def getSiret(self):
        pattern = r'[Ss][Ii][Rr][Ee][Tt].+?(\d{9} ?\d{5})\s'
        return self.regexSearch(pattern, [('siret', 1)])

    def getEverything(self):
        res = {}
        res.update(self.getValidityPeriod())
        res.update(self.getValidityEnd())
        res.update(self.getEmailAdress())
        res.update(self.getEmailAdress())
        res.update(self.getPhoneNumber())
        res.update(self.getSiren())
        res.update(self.getSiret())
        return res

    def checkValidity(self):
        # print(batiuniConnector.executeRequest('SELECT id FROM backBatiUni_userprofile', True))
        '''
            In order to check the coherence of the document, we want to compare it with the already gathered  data for this user.
        '''
        print("Extractor.checkValidity not implemented")


class QualibatExtractor(Extractor):
    '''
        Document très formatté
        Attention toutefois aux scans, qui pourraient induire des erreurs d'alignement, d'espacement, etc

        TODO : Codes et qualifications
    '''

    def getNumeroQualibat(self):
        pattern = r'[Nn][Uu][Mm][ÉéEe][Rr][Oo].+?(E-E\d+)'
        return self.regexSearch(pattern, [('numeroQualibat', 1)])

    def getCapital(self):
        pattern = r'[Cc][Aa][Pp][Ii][Tt][Aa][Ll]\s.*?\s(\d+([\. ]\d\d\d)*)\s+\D'
        return self.regexSearch(pattern, [('capital', 1)])

    def getRevenue(self):
        pattern = r'[Cc][Hh][Ii][Ff][Ff][Rr][Ee].*?\s(\d+([\. ]\d+)*)\s+\D'
        return self.regexSearch(pattern, [('revenue', 1)])

    def getNumeroCaisseCongesPayes(self):
        pattern = r'[Cc][Oo][Nn][Gg][ÉéEe][Ss]\s[Pp][Aa][Yy][ÉéEe][Ss][ :].+?(\d\w+?)\s'
        return self.regexSearch(pattern, [('numeroCaisseCongesPayes', 1)])

    def getAssuranceResponsabiliteTravaux(self):
        pattern = r'[Rr][ÉéEe][Ss][Pp][Oo][Nn][Ss][Aa][Bb][Ii][Ll][Ii][Tt][ÉéEe]\s[Tt][Rr][Aa][Vv][Aa][Uu][Xx].+?([A-Z][A-Z]+ .*?\d+)'
        return self.regexSearch(pattern, [('assuranceReponsabiliteTravaux', 1)])

    def getAssuranceResponsabiliteCivile(self):
        pattern = r'[Rr][ÉéEe][Ss][Pp][Oo][Nn][Ss][Aa][Bb][Ii][Ll][Ii][Tt][ÉéEe]\s[Cc][Ii][Vv][Ii][Ll][Ee].*?([A-Z][A-Z]+ .*?\d+)'
        return self.regexSearch(pattern, [('assuranceReponsabiliteCivile', 1)])

    def getEverything(self):
        res = super().getEverything()
        res.update(self.getNumeroQualibat())
        res.update(self.getCapital())
        res.update(self.getRevenue())
        res.update(self.getNumeroCaisseCongesPayes())
        res.update(self.getAssuranceResponsabiliteTravaux())
        res.update(self.getAssuranceResponsabiliteCivile())
        return res

    def checkValidity(self):
        Extractor.checkValidity(self)

class UrssafExtractor(Extractor):
    
    def getSecurityCode(self):
        pattern = r'([0-9A-Z]+)\s'
        return self.regexSearch(pattern, [('securityCode', 1)], header="CODE DE SÉCURITÉ")

    def getEverything(self):
        res = super().getEverything()
        res.update(self.getSecurityCode())
        return res

class KbisExtractor(Extractor):
    
    def getValidityEnd(self):
        pattern = r'qu\'au\s.*?(\d\d\/\d\d\/\d\d\d\d)'
        return self.regexSearch(pattern, [('validityEnd', 1)])

    def getSecurityCode(self):
        '''
            10 caractères alphanumériques
        '''
        pattern = r'(\w{10})\s'
        return self.regexSearch(pattern, [('securityCode', 1)], header="vérification")
    
    def getManagementNumber(self):
        pattern = r'(\d\d\d\d\w+)\s'
        return self.regexSearch(pattern, [('managementNumber', 1)], header="gestion")

    def getRcsNumber(self):
        pattern = r'(\d\d\d \d\d\d \d\d\d) R.C.S'
        return self.regexSearch(pattern, [('rcsNumber', 1)])

    def getEverything(self):
        res = super().getEverything()
        res.update(self.getSecurityCode())
        res.update(self.getManagementNumber())
        res.update(self.getRcsNumber())

        return res

    def checkValidity(self):
        '''
            Strat moche : 
                - Soit le code n'est pas reconnu
                - Soit le code est reconnu, mais le KBIS date de plus de 3 mois
                - Soit tout va bien
        '''
        from bs4 import BeautifulSoup
        res = self.getSecurityCode()
        if res['securityCode']:
            page_infogreffe = requests.get('https://www.infogreffe.fr/controle/verif?codeVerif='+res['securityCode']).text
            soup_infogreffe = BeautifulSoup(page_infogreffe, 'html.parser')
            links = soup_infogreffe.find('div', {"class":"verif"}).find_all("p", {"class":"spacer"})
            if(len(links)<4):
                return {"status": "error",
                        "code":res['securityCode'],
                        "message":"Aucun extrait de KBIS trouvé pour ce code de vérification."
                        }
            elif soup_infogreffe.find("p", {"class":"error"}):
                return {"status": "warning",
                        "code":res['securityCode'],
                        "message":"La commande de cet extrait de KBIS  est supérieure à 3 mois."
                        }
            else:
                return {'status': 'OK',
                        'code': res['securityCode'],
                        'message': 'Cet extrait de KBIS est valide, est date de moins de 3 mois.'
                        }

'''
doc1 = Extractor("C:\\Users\\Baptiste\\Documents\\Fantasiapp\\middleBatiuni\\assets\\attestation_rc_dc\\Attestation RC decennale .pdf")
doc2 = QualibatExtractor("C:\\Users\\Baptiste\\Documents\\Fantasiapp\\middleBatiuni\\assets\\qualibats\\qualibat_1.pdf")
'''
# extractor = QualibatExtractor('./assets/qualibats/qualibat_1.pdf')
# extractor = UrssafExtractor('../documents/urssaf/URSSAF 2020.pdf')
# extractor = KbisExtractor('./assets/kbis/KBIS 2021.pdf')

# data = extractor.getEverything()
# for field in data:
#     print('{:>30} {:<30}'.format(field, str(data[field])))

# extractor.checkValidity()

def testAllKbis():
    kbisDir = "../documents/kbis"
    for file in (os.path.join(kbisDir, file) for file in os.listdir(kbisDir)):
        print("Testing", file)
        print(KbisExtractor(file).checkValidity())

# testAllKbis()


extractor = UrssafExtractor('../documents/urssaf/URSSAF 2020.pdf')
data = extractor.getEverything()
for field in data:
    print('{:>30} {:<30}'.format(field, str(data[field])))














########################
# Exportable functions #
########################

#IT IS SO DUMB TO SORT WORDS BEFORE EACH SPLIT
def findSplit(words: list[TextElt], vertical: bool) -> Split:
    '''
        Given a list of words, find the best split (the criteria may change)
    '''

    coordinate, beginLine, endLine, criteria = 0, 9999, 0, 0
    block1, block2 = [], []
    (begin, end) = ('posX', 'endX') if vertical else ('posY', 'endY')

    beginSort = words[:]
    beginSort.sort(key=lambda x: getattr(x, begin))
    endSort = words[:]
    endSort.sort(key=lambda x: getattr(x, end))

    i, j, wSort = 0, 0, []
    while(i<len(beginSort) and j<len(endSort)):
        if(getattr(beginSort[i], begin) < getattr(endSort[j], end)):
            wSort.append((getattr(beginSort[i], begin), beginSort[i], True))
            i+=1
            
        else:
            wSort.append((getattr(endSort[j], end), endSort[j], False))
            j+=1
    
    if(i < len(beginSort)):
        while(i<len(beginSort)):
            wSort.append((getattr(beginSort[i], begin), beginSort[i], True))
            i+=1
    else:
        while(j<len(endSort)):
            wSort.append((getattr(endSort[j], end), endSort[j], False))
            j+=1

    #Used now to find the line boundaries
    (begin, end) = ('posY', 'endY') if vertical else ('posX', 'endX')

    opened = 0
    for k in range(len(wSort)):
        if(wSort[k][2] and getattr(wSort[k][1], begin)< beginLine): beginLine = getattr(wSort[k][1], begin)
        elif(getattr(wSort[k][1], end)> endLine): endLine = getattr(wSort[k][1], end)

        if wSort[k][2]:
            opened += 1
        else:
            opened -= 1
        
        if(wSort[k][2]):
            block2.append(wSort[k][1])

        
        if wSort[k][0] > wSort[0][0] and wSort[k][0] < wSort[-1][0] and opened == 0: #Allows to split at least one line...
        
            ## The criteria is the gap
            #
            if(wSort[k+1][0] - wSort[k][0] > criteria and (vertical or wSort[k][1].fontSize < wSort[k+1][1].fontSize or criteria==0)):
                coordinate = (wSort[k+1][0] + wSort[k][0])/2
                criteria = wSort[k+1][0] - wSort[k][0]
                block1 += block2[:]
                block2 = []

            ## The criteria is the length
            #
            

    return Split(criteria, block1, block2, vertical, (coordinate, beginLine, coordinate, endLine) if vertical else (beginLine, coordinate, endLine, coordinate))


def pruneTree(tree: Block)->Block:
    '''
        Prune the tree according to deterministic rules
    '''

    if(tree.isLeaf()):
        return tree

    left = pruneTree(tree.children[0])
    right = pruneTree(tree.children[1])

    if(left.words[-1].fontSize >= right.words[0].fontSize):
        tree.children = []

    return tree

def buildTree(words : list[TextElt], to_build: int, pruning: bool) -> list:
    '''
        Build a binary tree to_build+1 leaves
    '''
    tree = Block(0, (0, 0, 0, 0), words)
    dfs = [tree]

    for _ in range(to_build):
        best = None
        index = -1
        dfs = [tree]
        i = 0
        while i < len(dfs):
            block = dfs[i]
            dfs += block.children
            if(block.isLeaf()):
                block_words = block.words
                if(block_words != []):
                    splitH = findSplit(block_words, False)
                    splitV = findSplit(block_words, True)
                    
                    if splitV > splitH and (best is None or splitV > best):
                        best = splitV
                        index = i
                    elif best is None or splitH > best:
                        best = splitH
                        index = i
            i+=1
                
        if best is not None:
            dfs[index].children.append(Block(len(dfs)-1, dfs[index].line, best.block1))
            dfs[index].children.append(Block(len(dfs)-1, best.line, best.block2))

    return pruneTree(tree) if pruning else tree
