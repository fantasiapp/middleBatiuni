from importlib.metadata import files
from tkinter import *
from tkinter.messagebox import showinfo
from PIL import ImageTk, Image
import pickle
from clustering import Processer, Model, reduce_dimensions
from pdfExtraction import extractFullText
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC
import numpy as np
import random
import matplotlib.pyplot as plt

from os import listdir
from os.path import isfile, join

window = Tk()
window.geometry("1200x900")

processer = Processer()
doc2vec = Model('./saves/gensim.model')
doc2vec.load()

training_data = {
    'label': [],
    'embedding': []
}

IMG_PATH = './saves/svm2.png'
SVM_PATH = './saves/svm2.pkl'
mainDir ='..\documents'
pathList = [join(mainDir, dir, file) for dir in listdir(mainDir) for file in listdir(join(mainDir, dir)) if isfile(join(join(mainDir, dir), file)) and file.endswith('.pdf')]
random.shuffle(pathList)

img = ImageTk.PhotoImage(Image.open(IMG_PATH))

canvas = Canvas(window, width=img.width(), height=img.height())
image_container = canvas.create_image(0,0,anchor=NW, image=img)
canvas.pack()


filesList = Listbox(window, width=100, height=10)

def learn(_):
    path = pathList[filesList.curselection()[0]]
    label = path.split('\\')[2]
    print(f'{path} selected, its a {label}')
    training_data['label'].append(label)
    training_data['embedding'].append(doc2vec.buildEmbedding([processer.tokenize(extractFullText(path))])[0])
    pathList.pop(filesList.curselection()[0])
    filesList.delete(filesList.curselection()[0])

    try:
        x_vals, y_vals = reduce_dimensions(training_data['embedding'])
        X = [[x_vals[i], y_vals[i]] for i in range(len(x_vals))]
        clf = make_pipeline(StandardScaler(), SVC(gamma='auto'))
        clf.fit(X, training_data['label'])

        X = np.asarray(X)
        h=5
        x_min, x_max = min(X[:, 0]) - 1, max(X[:, 0]) + 1
        y_min, y_max = min(X[:, 1]) - 1, max(X[:, 1]) + 1

        xx, yy = np.meshgrid(np.arange(x_min, x_max, h),
                            np.arange(y_min, y_max, h))
        Z = clf.predict(np.c_[xx.ravel(), yy.ravel()])

        # Put the result into a color plot
        labelsChoices = list(set(training_data['label']))
        labels = [labelsChoices.index(label) for label in training_data['label']]
        
        Z = Z.reshape(xx.shape)
        for i in range(len(Z)):
            for j in range(len(Z[0])):
                Z[i][j] = labelsChoices.index(Z[i][j])
        plt.clf()
        plt.contourf(xx, yy, Z, cmap=plt.cm.coolwarm, alpha=0.8)


        # Plot also the training points
        plt.scatter(X[:, 0], X[:, 1], c=labels, cmap=plt.cm.coolwarm)
        plt.xlabel('Dimension 1')
        plt.ylabel('Dimension 2')
        plt.xlim(xx.min(), xx.max())
        plt.ylim(yy.min(), yy.max())
        plt.xticks(())
        plt.yticks(())

        plt.savefig(IMG_PATH)
    except:
        pass

learnBtn = Button(window, text='Learn', command=learn)
learnBtn.pack()

'''Initiate filesList'''
for i in range(len(pathList)):
    filesList.insert(i, pathList[i])
filesList.pack()
filesList.bind('<Double-Button>', learn)

window.mainloop()