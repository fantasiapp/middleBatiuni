from os import listdir
from os.path import isfile, join
from pandas.core.frame import DataFrame

import spacy
from nltk.corpus import stopwords
from gensim.models import Word2Vec
import numpy as np
from sklearn.manifold import TSNE
import matplotlib.pyplot as plt
import random
import pandas as pd

from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC
from sklearn.model_selection import train_test_split
import pickle

from ie import *
from decorators import timer

mainDir = '../documents'

def loadFiles(nbFiles: int = 0) -> dict[str, list[str]]:
    return {dir: [join(mainDir, dir, file) for file in (listdir(join(mainDir, dir))[:nbFiles] if nbFiles else listdir(join(mainDir, dir))) if isfile(join(join(mainDir, dir), file)) and file.endswith('.pdf')] for dir in listdir(mainDir)}

@timer
def buildCorpus(files: list[str]) -> list[str]:
    return [extractFullText(file) for file in files]

class Processer:
    '''
        Used to tokenize the documents
        As the initialisation is heavy, should be instantiated as little as possible
    '''
    def __init__(self):
        self.stopwords = stopwords.words('english')
        self.nlp = spacy.load("fr_core_news_md")
        print("Processer initialization complete")

    @timer
    def tokenize(self, text: str) -> str:
        '''
            Removes french and english stopwords, some punctuation, and lemmas shorter than 2
        '''
        doc = self.nlp(text)
        tokens = [token.lemma_.lower() for token in doc
                     if token.lemma_ not in self.stopwords
                     and token.is_stop == False
                     and token.is_punct == False
                     and token.lemma_.isalnum()
                     and not token.lemma_.isdecimal()]

        return [token for token in tokens if len(token)>2]

def buildTokensList(processer: Processer, corpus: list[list[str]]):
    return [processer.tokenize(text) for text in corpus]

class Model:
    '''
        Trains or load a Word2Vec model
    '''

    def __init__(self, save_path):
        self.save_path = save_path
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

class Data:

    def __init__(self, path):
        self.path = path
        self.df = pd.DataFrame()
    
    def load(self):
        self.df = pd.read_csv(self.path)

    def save(self):
        self.df.to_csv(self.path)

    def setPath(self, paths : list[str]):
        self.df['path'] = paths

    def setEmbedding(self, embeddings: list[list[float]]):
        self.df['embedding'] = embeddings

    def setLabel(self, labels : list[str]):
        self.df['label'] = labels

def reduce_dimensions(vectors, num_dimensions: int = 2, output_dimensions: tuple[int, int] = (0,1)):
    num_dimensions = num_dimensions  # final num dimensions (2D, 3D, etc)
    

    # extract the words & their vectors, as numpy arrays
    vectors = np.asarray(vectors)

    # reduce using t-SNE
    tsne = TSNE(n_components=num_dimensions, random_state=0)
    vectors = tsne.fit_transform(vectors)

    x_vals = [v[output_dimensions[0]] for v in vectors]
    y_vals = [v[output_dimensions[1]] for v in vectors]
    return x_vals, y_vals

def plot_with_matplotlib(x_vals: list[float], y_vals: list[float], data):

    fig, ax = plt.subplots()
    colors = {}
    for label in data:
        colors[label] = [np.random.random() for i in range(3)]
    c = [colors[label] for label in data for i in range(len(data[label]))]

    ax.scatter(x_vals, y_vals, c=c)
    offset = 0
    fig.suptitle(f'Mapping of {len(x_vals)} documents')
    for label in data:
        ax.text(-85, 40+offset, label, fontsize=8,  color=colors[label])
        offset+=10
    plt.savefig('./saves/fig.png')


def extractData(nbFiles: int = 0):
    filesDict = loadFiles(nbFiles)
    processer = Processer()
    keys = filesDict.keys()
    
    dataStorage = Data('./saves/dataframe.csv')
    dataStorage.setPath([path for key in keys for path in filesDict[key]])

    for key in keys:
        print(f'Extracting texts from file {key}')
        filesDict[key] = buildCorpus(filesDict[key])
        print(f'Tokenizing texts from corpus {key}')
        filesDict[key] = [processer.tokenize(text) for text in filesDict[key]]

    # df['tokens'] = [tokens for key in keys for tokens in filesDict[key]]

    doc2vec = Model('./saves/gensim.model')
    doc2vec.trainModel([tokens for key in keys for tokens in filesDict[key]])
    doc2vec.save()

    for key in keys:
        filesDict[key] = doc2vec.buildEmbedding(filesDict[key])

    vectors = [embedding for key in keys for embedding in filesDict[key]]
    labels =  [key for key in keys for i in range(len(filesDict[key]))]

    dataStorage.setEmbedding(vectors)
    dataStorage.setLabel(labels)

    dataStorage.save()


@timer
def learnClf():
    df = pd.read_csv('./saves/dataframe.csv')
    labels = df['label'].unique()
    data = {}
    for label in labels:
        data[label] = df[df['label']==label]['embedding']

    vectors = [[float(v.strip('\n\r')) for v in vector.strip(' []').split(' ') if v!=''] for label in labels for vector in data[label]]
    labels = [label for label in labels for i in range(len(data[label]))]

    clf = make_pipeline(StandardScaler(), SVC(gamma='auto'))
    X_train, X_test, y_train, y_test = train_test_split(vectors, labels, test_size=0.33, random_state=42)
    clf.fit(X_train, y_train)
    score = clf.score(X_test, y_test)
    print(f'Test score : {score}')
    with open('./saves/svm.pkl', 'wb') as f:
        pickle.dump(clf, f)

@timer
def predict(files: list[str]):
    # print(f'Predicting {file}')
    processer = Processer()
    
    doc2vec = Model('./saves/gensim.model')
    doc2vec.load()
    corpus = [extractFullText(file) for file in files]
    tokensList = [processer.tokenize(text) for text in corpus]
    embeddingList = doc2vec.buildEmbedding(tokensList)
    
    with open('./saves/svm.pkl', 'rb') as clfFile:
        clf = pickle.load(clfFile)
    predictions = clf.predict(embeddingList)
    for file, prediction in zip(files, predictions):
        print(f'{file} has been found to be a {prediction}')

files = [join('./assets', file) for file in listdir('./assets/') if isfile(join('./assets', file)) and file.endswith('.pdf')]
predict(files)