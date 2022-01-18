from cProfile import label
from os import listdir, replace
from os.path import isfile, join, dirname, abspath

import spacy
from nltk.corpus import stopwords
from gensim.models import Word2Vec
import numpy as np
from sklearn.manifold import TSNE
import pandas as pd
import hashlib

from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC
from sklearn.model_selection import train_test_split
import pickle

from ie import *

"""
    [ How it works ]
        
        * Initial training * 
        Must be performed at least once
        
            - extractData() : Trains a word2vec model from scratch with every classified documents available on the server.
            It extracts text from files, tokens froms text, and learns an effective embedding.
            Stores the paths, labels, tokens, embedding and the text hash for each of these documents.
                
            - learnClf(DataFrame, Path) : Trains a SVM with the specified DataFrame.

        * Further training *

            - retrainModel() : Retrains the word2vec model without reprocessing the documents, thanks to the stored DataFrame
        
        * Application interactions *

            - predict(files: list[str]) : loads the SVM classifier, and predicts the labels for the input files

            - addToCsv(inputPath: str, files: list[str], labels: list[str], embeddingList: list[list[float]], tokensList: list[list[str]], hashes: list)
                May be called after predict. It adds the recently processed files to the stored DataFrame.
"""

package_directory = dirname(abspath(__file__))


def loadFiles(nbFiles: int = 0) -> dict[str, list[str]]:
    mainDir = join(package_directory, '../documents')
    return {dir: [join(mainDir, dir, file) for file in (listdir(join(mainDir, dir))[:nbFiles] if nbFiles else listdir(join(mainDir, dir))) if isfile(join(join(mainDir, dir), file)) and file.endswith('.pdf')] for dir in listdir(mainDir)}

@extractFullText.startCount
def buildCorpus(files: list[str]) -> list[str]:
    return [extractFullText(file) for file in files]

class Processer:
    '''
        Used to tokenize the documents
        As the initialisation is heavy, should be instantiated as little as possible
    '''

    def __init__(self, modelFile = join(package_directory, 'saves/gensim.model'), dataFile = join(package_directory, 'saves/dataframe.csv'), clfFile = join(package_directory, 'saves/svm.pkl')):
        self.stopwords = stopwords.words('english')
        self.nlp = spacy.load("fr_core_news_md")
        self.modelFile = modelFile
        self.dataFile = dataFile
        self.clfFile = clfFile
       

        self.tempData = {}
        self.storedData = Data(dataFile)
        print("Processer initialization complete")


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

    @classmethod
    def hashText(cls, text: str):
        return hashlib.sha224(text.encode('utf-8')).digest()

    def buildTokensList(self, corpus: list[list[str]]):
        return [self.tokenize(text) for text in corpus]

    def extractData(self, nbFiles: int = 0):
        '''
            Used rebuild to full doc2vec model
            As it is a long and painful process, chose your moment wisely
        '''
        filesDict = loadFiles(nbFiles)
        keys = filesDict.keys()

        self.storedData.setPath([path for key in keys for path in filesDict[key]])

        hashesDict = {}
        for key in keys:
            print(f'Extracting texts from directory {key}')
            filesDict[key] = buildCorpus(filesDict[key])
            hashesDict[key] = [Processer.hashText(text) for text in filesDict[key]]
            filesDict[key] = [self.tokenize(text) for text in filesDict[key]]

        doc2vec = Model(self.modelFile)
        doc2vec.trainModel([tokens for key in keys for tokens in filesDict[key]])
        doc2vec.save()

        self.storedData.setTokens([tokens for key in keys for tokens in filesDict[key]])

        for key in keys:
            filesDict[key] = doc2vec.buildEmbedding(filesDict[key])

        vectors = [embedding for key in keys for embedding in filesDict[key]]
        labels =  [key for key in keys for i in range(len(filesDict[key]))]
        hashes = [hash for key in filesDict for hash in hashesDict[key]]
        self.storedData.setEmbedding(vectors)
        self.storedData.setLabel(labels)
        self.storedData.setHash(hashes)
        self.storedData.save()

    def retrainModel(self):
        self.storedData.load()
        doc2vec = Model(self.modelFile)
        doc2vec.trainModel([token for tokens in self.storedData.getTokens() for token in tokens])
        doc2vec.save()

        self.storedData.setEmbedding(doc2vec.buildEmbedding(self.storedData.getTokens()))
        self.storedData.save()
    
    def learnClf(self):
        self.storedData.load()

        labels = self.storedData.getLabel().unique()
        data = {}
        for label in labels:
            data[label] = [Data.unformatEmbedding(vector) for vector in self.storedData.df[self.storedData.df['label']==label]['embedding']]

        vectors = [vector for label in labels for vector in data[label]]
        labels = [label for label in labels for _ in range(len(data[label]))]

        clf = make_pipeline(StandardScaler(), SVC(gamma='auto'))
        X_train, X_test, y_train, y_test = train_test_split(vectors, labels, test_size=0.33, random_state=42)
        clf.fit(X_train, y_train)
        score = clf.score(X_test, y_test)
        print(f'Test score : {score}')
        with open(self.clfFile, 'wb') as f:
            pickle.dump(clf, f)
        return clf

    def predict(self, files: list[str]):
        
        doc2vec = Model(self.modelFile)
        doc2vec.load()
        corpus = buildCorpus(files)
        tokensList = [self.tokenize(text) for text in corpus]
        embeddingList = doc2vec.buildEmbedding(tokensList)
        
        with open(self.clfFile, 'rb') as clfFile:
            clf = pickle.load(clfFile)
        predictions = clf.predict(embeddingList)
        
        for file, prediction in zip(files, predictions):
            print(f'{file} has been found to be a {prediction}')
        
        for i in range(len(files)):
            self.tempData[files[i]] = {
                'tokens': tokensList[i],
                'embedding': embeddingList[i],
                'hash': Processer.hashText(corpus[i])
            }
        
        return predictions
    
    def addToCsv(self, files: list[str], labels: list[str]):
        self.storedData.load()

        for i in range(len(files)):
            for match in self.storedData.getHash()==str(self.tempData[files[i]]['hash']):
                if match:
                    self.tempData[files[i]]['isNew'] = True
                    replace(files[i], join(join(package_directory, '../documents/') + labels[i], files[i].strip('/').split('/')[-1]))

        dataToStore = Data(self.dataFile)
        dataToStore.setPath(self.storedData.getPath() + [files[i] for i in range(len(files)) if self.tempData[files[i]]['isNew']])
        dataToStore.setLabel(self.storedData.getLabel() + [labels[i] for i in range(len(files)) if self.tempData[files[i]]['isNew']])
        dataToStore.setEmbedding(self.storedData.getEmbedding() + [self.tempData[files[i]]['embedding'] for i in range(len(files)) if self.tempData[files[i]]['isNew']])
        dataToStore.setTokens(self.storedData.getTokens() + [self.tempData[files[i]]['tokens'] for i in range(len(files)) if self.tempData[files[i]]['isNew']])
        dataToStore.setHash(self.storedData.getHash() + [self.tempData[files[i]]['hash'] for i in range(len(files)) if self.tempData[files[i]]['isNew']])
        dataToStore.save()
        
        self.storedData = dataToStore

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
    def getPath(self) -> list[str]:
        return self.df['path'].to_list()

    def setTokens(self, tokensList: list[list[str]]):
        self.df['tokens'] = tokensList
    def getTokens(self) -> list[list[str]]:
        return [[token.strip('\'') for token in tokens.strip('[]').split(', ')] for tokens in self.df['tokens']]

    def setEmbedding(self, embeddings: list[list[float]]):
        self.df['embedding'] = embeddings
    def getEmbedding(self) -> list[list[float]]:
        return [Data.unformatEmbedding(vector) for vector in self.df['embedding']]

    def setLabel(self, labels : list[str]):
        self.df['label'] = labels
    def getLabel(self) -> list[str]:
        return self.df['label'].to_list()

    def setHash(self, hashes: list[str]):
        self.df['hash'] = hashes
    def getHash(self) -> list[str]:
        return self.df['hash'].to_list()

    @classmethod
    def unformatEmbedding(cls, embeddingString: str) -> list[float]:
        return [float(v.strip('\n\r')) for v in embeddingString.strip(' []').split(' ') if v!='']


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
