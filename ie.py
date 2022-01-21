from pdfExtraction import *


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
