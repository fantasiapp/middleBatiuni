from os import listdir
from os.path import isfile, join

import spacy
from nltk.corpus import stopwords
from gensim.models import Word2Vec
import numpy as np
from sklearn.manifold import TSNE
import matplotlib.pyplot as plt
import random
import pandas as pd

from ie import *
from decorators import timer

mainDir = '../documents'

@timer
def loadFiles(nbFiles: int = 0) -> dict[str, list[str]]:
    return {dir: [join(mainDir, dir, file) for file in (listdir(join(mainDir, dir))[:nbFiles] if nbFiles else listdir(join(mainDir, dir))) if isfile(join(join(mainDir, dir), file)) and file.endswith('.pdf')] for dir in listdir(mainDir)}

@timer
def buildCorpus(files: list[str]) -> list[list[str]]:
    return [extractFullText(file) for file in files]

class Processer:

    def __init__(self):
        self.stopwords = stopwords.words('english')
        self.nlp = spacy.load("fr_core_news_md")
        
        print("Processer initialization complete")

    @timer
    def tokenize(self, text: str) -> str:
        doc = self.nlp(text)
        tokens = [token.lemma_.lower() for token in doc
                     if token.lemma_ not in self.stopwords
                     and token.is_stop == False
                     and token.is_punct == False]

        return [token for token in tokens if len(token)>2]

# processer = Processer()

def buildTokensList(processer: Processer, corpus: list[list[str]]):
    return [processer.tokenize(text) for text in corpus]

class Model:
    '''
        Trains or load a Word2Vec model
    '''

    def __init__(self):
        self.save_path = './saves/gensim.model'
        self.min_count=3
        self.vector_size=50
        self.sg=1
        self.window=7
        self.epochs=40

    @timer
    def trainModel(self, tokensList):
        self.model = Word2Vec(
                tokensList,
                min_count=self.min_count,   # Ignore words that appear less than this
                vector_size=self.vector_size,       # Dimensionality of word embeddings
                sg =self.sg,        # skipgrams
                window=self.window,      # Context window for words during training
                epochs=self.epochs)       # Number of epochs training over corpus

        print('Training complete')

    def save(self):
        self.model.save(self.save_path)
        print(f'Model saved in {self.save_path}')
    
    def load(self):
        self.model = Word2Vec.load(self.save_path)
        print(f'Model loaded from {self.save_path}')

    @timer
    def buildEmbedding(self, tokensList):
        embedding = []
        for tokens in tokensList:
            sum = np.array(self.vector_size*[0.])
            for token in tokens:
                if token in self.model.wv.key_to_index:
                    sum += self.model.wv[token]
            embedding.append(sum)
        
        return embedding


def reduce_dimensions(vectors, labels, num_dimensions: int = 2, output_dimensions: tuple[int, int] = (0,1)):
    num_dimensions = num_dimensions  # final num dimensions (2D, 3D, etc)
    

    # extract the words & their vectors, as numpy arrays
    vectors = np.asarray(vectors)
    labels = np.asarray(labels)  # fixed-width numpy strings

    # reduce using t-SNE
    tsne = TSNE(n_components=num_dimensions, random_state=0)
    vectors = tsne.fit_transform(vectors)

    x_vals = [v[output_dimensions[0]] for v in vectors]
    y_vals = [v[output_dimensions[1]] for v in vectors]
    return x_vals, y_vals, labels

def plot_with_matplotlib(x_vals: list[float], y_vals: list[float], labels, nbLabels: int = 25):

    nbLabels = min(nbLabels, len(labels))

    random.seed(0)

    plt.figure(figsize=(12, 12))
    plt.scatter(x_vals, y_vals)

    #
    # Label randomly subsampled 25 data points
    #
    indices = list(range(len(labels)))
    selected_indices = random.sample(indices, nbLabels)
    for i in selected_indices:
        plt.annotate(labels[i], (x_vals[i], y_vals[i]))
    plt.savefig('./saves/fig.png')


def extractData(nbFiles: int = 0):
    filesDict = loadFiles(nbFiles)
    processer = Processer()
    keys = filesDict.keys()
    
    df = pd.DataFrame()
    df['path'] = [path for key in keys for path in filesDict[key]]

    for key in keys:
        print(f'Extracting texts from file {key}')
        filesDict[key] = buildCorpus(filesDict[key])
        print(f'Tokenizing texts from corpus {key}')
        filesDict[key] = [processer.tokenize(text) for text in filesDict[key]]

    # df['tokens'] = [tokens for key in keys for tokens in filesDict[key]]

    doc2vec = Model()
    doc2vec.trainModel([tokens for key in keys for tokens in filesDict[key]])
    doc2vec.save()

    for key in keys:
        filesDict[key] = doc2vec.buildEmbedding(filesDict[key])

    vectors = [embedding for key in keys for embedding in filesDict[key]]
    labels =  [key for key in keys for i in range(len(filesDict[key]))]

    df['embedding'] = vectors

    x_vals, y_vals, labels = reduce_dimensions(vectors, labels)
    plot_with_matplotlib(x_vals, y_vals, labels)
    df['label'] = labels
    df.to_csv('./saves/dataframe.csv')
    
'''
    CAREFUL BEFORE UNCOMMENT
    # extractData()
'''

# Next to do : compute better img, with correct colors and labelling
