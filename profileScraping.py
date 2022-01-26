import requests
import csv

from decorators import *
import os
import sys

NAF_classe_dict = {}
NAF_sous_classe_dict = {}

package_directory = os.path.dirname(os.path.abspath(__file__))

from bdd import DBConnector
sireneConnector = DBConnector('Sirene')

import spell
'''
    Load dictionaries to match NAF codes and activity denomination
'''
reader = csv.reader(open(os.path.join(package_directory, 'assets/naf2008-liste-n4-classes.csv'), 'r', encoding='UTF-8'))
for row in reader:
   k, v = row
   NAF_classe_dict[k] = v

reader = csv.reader(open(os.path.join(package_directory, 'assets/naf2008-liste-n5-sous-classes.csv'), 'r', encoding='UTF-8'))
for row in reader:
   k, v = row
   NAF_sous_classe_dict[k] = v

def getClasseByNAF(code: str) -> str:
    return NAF_classe_dict.get(code)

def getSousClasseByNAF(code: str) -> str:
    return NAF_sous_classe_dict.get(code)

def querySearchEtablissemenstBySiren(siren: str):
    return f'SELECT siret, nic, activitePrincipaleEtablissement, numeroVoieEtablissement, typeVoieEtablissement, libelleVoieEtablissement, codePostalEtablissement, libelleCommuneEtablissement FROM etablissements WHERE siren LIKE "{siren}"'

def handleSearchEtablissementsBySiren(resList: list):
    pass

def querySearchUnitesLegalesByDenomination(denomination: str):
    return f'SELECT siren, activitePrincipaleUniteLegale, nicSiegeUniteLegale FROM unites_legales,  WHERE denominationUniteLegale LIKE "{denomination}" LIMIT 10'

def handleSearchUnitesLegalesByDenomination(resList: list):
    pass

def querySearchEstablishmentsByDenomination(denomination: str):
    return f'SELECT denominationUniteLegale, numeroVoieEtablissement, typeVoieEtablissement, libelleVoieEtablissement, codePostalEtablissement, libelleCommuneEtablissement, activitePrincipaleEtablissement, siret, etablissements.siren  FROM etablissements JOIN unites_legales ON etablissements.siren=unites_legales.siren WHERE denominationUniteLegale LIKE "{denomination}%" LIMIT 50'


def handleSearchEstablishmentsByDenomination(resList: list):
    for i in range(len(resList)):
        res = resList[i]
        siren = res[8]
        cleTva = (12+(3*int(siren)%97))%97
        resList[i] = [res[0], f'{res[1]} {res[2]} {res[3]}, {res[4]} {res[5]}', getSousClasseByNAF(res[6]) or getClasseByNAF(res[6]) or "Activité inconnue", res[7], f'FR{cleTva}{siren}']
    return {
        'EstablishmentsFields': ['nom', 'adresse', 'activitePrincipale', 'siret', 'NTVAI'],
        'EstablishmentsValues': {i: resList[i] for i in range(len(resList))
        }
    }

def getEnterpriseDataFrom(siren = None, siret=None, subName=None):
    
    if subName:
        query = querySearchEstablishmentsByDenomination(spell.correction(subName.upper()))
        handler = handleSearchEstablishmentsByDenomination
    elif siren:
        pass
    elif siret:
        pass
    
    status, msg, data = "error", "An unexpected error occured", {'EstablishmentsFields': [], 'EstablishmentsValues': {}}
    try:
        resList = sireneConnector.executeRequest(query, dml=True)
        if not resList:
            status = "info"
            msg = "Aucun résultat ne semble porter ce nom."
        else:
            status="OK"
            msg="Oll Korrekt"
            data = handler(resList)
    except:
        print("Something wrong happened ...")
    return {
        'status': status,
        'msg': msg,
        'data': data
    }
