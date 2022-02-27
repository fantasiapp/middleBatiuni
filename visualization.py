from clustering import *
from wordcloud import WordCloud
import matplotlib.pyplot as plt


'''
    Population overview
'''

def visualizePopulation():
    filesDict = loadFiles()
    names = [label for label in filesDict]
    values = [len(filesDict[label]) for label in filesDict]
    colors = [(np.random.random(), np.random.random(), np.random.random()) for label in filesDict]

    plt.bar(names, values, color=colors)
    plt.savefig('./saves/bar.png')

'''
    WordCloud
'''

def generateWC(text: str, stopwords = []) -> WordCloud:

    wordcloud = WordCloud(random_state = 42,
        normalize_plurals=False,
        width=600, height=300,
        max_words=300,
        stopwords=stopwords
    )

    wordcloud.generate(text)

    return wordcloud

def displayWC(wordcloud: WordCloud) -> None:
    fig, ax = plt.subplots(1, 1, figsize=(9,6))
    plt.imshow(wordcloud, interpolation='bilinear')
    plt.axis("off")
    plt.savefig('./saves/wordcloud.png')

def visualizeWC():
    processer = Processer()
    sample_corpus = [processer.tokenize(extractFullText(file)) for label in filesDict for file in np.random.choice(filesDict[label], min(50, len(filesDict[label])))]
    displayWC(generateWC(' '.join([token for tokens in sample_corpus for token in tokens])))

'''
    SVM
'''

def visualizeSVM():
    dataStorage = Data('./saves/dataframe.csv')
    dataStorage.load()

    embeddings = [[float(v.strip('\n\r')) for v in vector.strip(' []').split(' ') if v!=''] for vector in dataStorage.df['embedding']]
    labels = dataStorage.df['label']

    x_vals, y_vals = reduce_dimensions(embeddings)
    clf = make_pipeline(StandardScaler(), SVC(gamma='auto'))
    X_train, X_test, y_train, y_test = train_test_split([[x_vals[i], y_vals[i]] for i in range(len(x_vals))], labels, test_size=0.33, random_state=42)
    clf.fit(X_train, y_train)

    X_test = np.asarray(X_test)

    h=.5
    x_min, x_max = min(X_test[:, 0]) - 1, max(X_test[:, 0]) + 1
    y_min, y_max = min(X_test[:, 1]) - 1, max(X_test[:, 1]) + 1

    xx, yy = np.meshgrid(np.arange(x_min, x_max, h),
                        np.arange(y_min, y_max, h))
    Z = clf.predict(np.c_[xx.ravel(), yy.ravel()])

    # Put the result into a color plot
    Z = Z.reshape(xx.shape)
    uniques = list(set(y_test))
    for i in range(len(Z)):
        for j in range(len(Z[0])):
            Z[i][j] = uniques.index(Z[i][j])

    plt.contourf(xx, yy, Z, cmap=plt.cm.coolwarm, alpha=0.8)

    # Plot also the training points
    colors = {}
    for label in uniques:
        colors[label] = [np.random.random() for _ in range(3)]
    
    c = [colors[y] for y in y_test]

    plt.scatter(X_test[:, 0], X_test[:, 1], c=c, marker=(5,0), cmap=plt.cm.coolwarm)
    plt.xlabel('Dimension 1')
    plt.ylabel('Dimension 2')
    plt.xlim(xx.min(), xx.max())
    plt.ylim(yy.min(), yy.max())
    plt.xticks(())
    plt.yticks(())

    plt.savefig('./saves/svm.png')

visualizePopulation()
visualizeSVM()
