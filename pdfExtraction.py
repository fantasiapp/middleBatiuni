from PyPDF2.generic import ArrayObject, NumberObject

from pdfminer.high_level import extract_pages, extract_text
from pdfminer.layout import LTTextContainer, LTChar, LTPage, LTFigure, LTImage, LTAnno

import random


def randomColor():
    return (int(random.random()*255), int(random.random()*255), int(random.random()*255))

def getPageDimensions(file): #usefull ?
    '''
        Returns the dimensions of a pdf document
    '''
    page_layout = next(extract_pages(file))
    return (page_layout.width, page_layout.height)


class TextElt:
    '''
        This may store lines, words or characters
        Also stores the font characteristics, and the position
    '''
    
    posX, posY, endX, endY, fontSize = 0, 0, 0, 0, 0
    textValue, fontName = '', ''
    font = None

    def __init__(self, posX, posY, endX, endY, fontSize, textValue, fontColor):
        self.posX, self.posY, self.fontSize, self.textValue, self.fontColor = posX, posY, fontSize, textValue, fontColor
        self.endX = endX
        self.endY = self.posY + fontSize

    def setFont(self, font):
        self.font = font

    def getFont(self):
        return self.font

    def getDimensions(self):
        return self.font.size(self.textValue)

    def getWidth(self):
        return self.getDimensions()[0]
    
    def getHeight(self):
        return self.getDimensions()[1]

def extractFirstPageLayout(file: str) ->LTPage:
    return next(extract_pages(file))# for now, only reading the first page


def extractTextElts(file: str, sliceIt: bool = False) -> list:
    # if sliceIt is True, it will consider each word seperately
    # if False, it'll consider each line as a word

    textElts = []
    TLX, TLY, BRX, BRY = 0,0,0,0

    # for page_layout in extract_pages(current_resume):
    page_layout = extractFirstPageLayout(file)
    for element in page_layout:
        if isinstance(element, LTTextContainer):
            for text_line in element:
                if not isinstance(text_line, LTAnno):
                    inAWord = False
                    word = ''
                    x0, y0, x1, y1 = text_line.x0, text_line.y0, text_line.x1, text_line.y1
                    fontSize  = 10

                    if sliceIt and not isinstance(text_line, LTChar): #ignore line with one only char
                        for character in text_line:
                            if(isinstance(character, LTChar) and str.isalnum(character.get_text())):
                                if(inAWord == False): #A new word
                                    if(word != ''):
                                        textElts.append(TextElt(x0, page_layout.height - y0, x1, y1, fontSize, word, randomColor()))
                                        TLX = min(x0, TLX)
                                        TLY = max(y0, TLY)
                                        BRX = max(character.x1, BRX)
                                        BRY = min(character.y1, BRY)
                                    word = ''
                                    x0, y0 = character.bbox[0], character.bbox[1]
                                    fontSize = character.size
                                    inAWord = True

                                x1, y1 = character.bbox[2], character.bbox[3]
                                word+=character.get_text()
                            else:
                                inAWord = False

                        if(word != ''):
                            textElts.append(TextElt(x0, page_layout.height - y0, x1, y1, fontSize, word, randomColor()))
                    else:
                        textElts.append(TextElt(x0, page_layout.height - y0, x1, y1, fontSize, text_line.get_text(), randomColor()))

    return textElts


def extractFullText(file: str, sorted: bool = False) -> str:
    '''
        Returns the full text of a file
        Could Implemented the possibility to sort the words (for now vertically, then horizontally, which may be far from the layout)
    '''
    print(f"Extract text from {file}")
    try:
        return extract_text(file)
    except:
        print(f"Could not load the PDF ...")
        return ""
        

def extractImages(file: str) -> list[tuple[float, float, float, float]]:
    imagesBbox = []
    page_layout = extractFirstPageLayout(file)
    for element in page_layout:
        if isinstance(element, LTImage) or isinstance(element, LTFigure):
            imagesBbox.append((element.x0, page_layout.height - element.y1, element.width, element.height))

    return imagesBbox