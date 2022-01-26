from bdd import *
sireneConnector = DBConnector('Sirene')

import csv

def buildFromCsv(csvpath: str, tableName: str):
    names = []

    with open(csvpath) as csvfile:
        datareader=csv.reader(csvfile)
        names=next(datareader)

    sireneConnector.createTable(tableName, [Column(name, "varchar", 255) for name in names])
    
    sireneConnector.describeDB()

    query=f'LOAD DATA LOCAL INFILE "{csvpath}" INTO {tableName} FIELDS TERMINATED BY "," LINES TERMINATED BY "\r\n" IGNORE 1 LINES;'
    query="LOAD DATA LOCAL INFILE '" + csvpath + "' INTO TABLE " + tableName + " FIELDS TERMINATED BY ',' IGNORE 1 LINES;"
    sireneConnector.executeRequest(query)

'''
    CAREFUL BEFORE UNCOMMENTING

#buildFromCsv("./storage/StockUniteLegale_utf8.csv", "unites_legales")
'''
import pandas as pd
df = pd.read_csv('./work/saves/dataframe.csv')

def buildTableDocuments():
    sireneConnector.dropTable('documents')
    sireneConnector.createTable('documents', [
        Column('id', "int", auto_increment=True),
        Column('path', "varchar", data_length=256),
        Column('hash', "int"),
        Column('label_id', "int")],
        constraints = ["PRIMARY KEY(id)"])

def buildTableLabels():
    sireneConnector.dropTable('labels')
    sireneConnector.createTable('labels', [
        Column('id', "int"),
        Column('name', "varchar", data_length=50)],
        consttaints = ["PRIMARY KEY(id)"])

def insertTableLabels(i: int, label: str):
    sireneConnector.executeRequest(f"INSERT INTO labels (id, name) VALUES ('{i}', '{label}')")

def fillTableLabels():
    labels = list(df['label'].unique())
    for i, label in enumerate(labels):
        insertTableLabels(i, label)

def buildTableEmbeddings():
    nbDimensions = 50
    sireneConnector.dropTable('embeddings')
    sireneConnector.createTable('embeddings', [Column('doc_id', "int")] + [Column(f'dim{i}', "float") for i in range(1, nbDimensions+1)])

def fillTables():
    fillTableLabels()
    paths = df['path']
    for path in paths:
        label = list(df[df['path']==path]['label'])[0]
        label_id = sireneConnector.executeRequest(f'SELECT id FROM labels WHERE name LIKE "{label}"', True)[0][0]
        query = f'INSERT INTO documents (path, label_id) VALUES ("{path}", "{label_id}")'
        sireneConnector.executeRequest(query)
    
        embedding = [float(v.strip('\n\r')) for v in list(df[df['path']==path]['embedding'])[0].strip(' []').split(' ') if v!='']

        doc_id = sireneConnector.executeRequest(f'SELECT id FROM documents WHERE path LIKE "{path}"', True)[0][0]
    
        fields = "(doc_id"
        values = f"('{doc_id}'"
        for i,v in enumerate(embedding):
            fields+=f", dim{i+1}"
            values+=f", '{v}'"
        fields += ")"
        values += ")"

        sireneConnector.executeRequest(f"INSERT INTO embeddings {fields} VALUES {values}")

def buildDbData():
    buildTableDocuments()
    buildTableLabels()
    buildTableEmbeddings()
    fillTables()

'''
for e in sireneConnector.executeRequest("SELECT * FROM embeddings WHERE doc_id IN (SELECT id FROM documents WHERE label_id IN (SELECT id FROM labels WHERE name LIKE 'attestation_travail_dissimule'))", True):
    print(e)
'''


fields = ', '.join([f"e.dim{i}" for i in range(1, 51)])
'''
print(sireneConnector.executeRequest(f"SELECT {fields} FROM embeddings", True))
'''

results = sireneConnector.executeRequest(f"SELECT j.name, {fields} FROM embeddings AS e JOIN (SELECT d.id, l.name FROM documents AS d JOIN labels AS l ON d.label_id = l.id) AS j ON j.id = e.doc_id", True)
print([row[0] for row in results])
