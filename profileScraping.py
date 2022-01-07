import requests
import csv
import os
import sys

from bdd import executeRequest

NAF_classe_dict = {}
NAF_sous_classe_dict = {}

package_directory = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(package_directory, '..'))

import bdd

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

class LegalUnit:

    fields = ['denomination', 'activite_principale', 'adresse_siege', 'siren', 'siret_siege']

    def extractFields(data: dict) -> dict:
        return {
            'denomination': data['denomination'],
            'activite_principale': getSousClasseByNAF(data["activite_principale"]) or getClasseByNAF(data["activite_principale"]),
            'adresse_siege': data['etablissement_siege']['geo_adresse'],
            'siren': data['siren'],
            'siret_siege': data['etablissement_siege']['siret']
        }

    @classmethod
    def getFields(cls) -> list[str]:
        return cls.fields

def searchUnitesLegalesByDenomination(denomination: str) -> dict:
    '''
        Recherche les unités légales qui s'écrivent exactement avec cette dénomination (à la normalisation près)
        Retour sous la forme d'un dictionnaire avec une clé "error" ou "unites_legales" selon le succès de la requête
    '''

    denomination = str(denomination).upper()
    
    params = { 
        'action': 'query', 
        'format': 'json',
        'denomination': denomination,
        'prop': 'extracts', 
        'explaintext': True
    }

    resList = executeRequest(f'SELECT siren, siret FROM etablissement WHERE denominationUsuelleEtablissement IS {denomination}')

    response = requests.get(
         'https://entreprise.data.gouv.fr/api/sirene/v3/unites_legales',
         params= params
    )
    if(response.status_code == 200):
        results = response.json()
        if len(results) > 0:
            status = 'info'
            msg = 'Not enough informations'
        else:
            status = 'ok'
            data = [LegalUnit.extractFields(data) for data in results['unites_legales']]
            msg = ""
    elif(response.status_code == 404):
        status = 'warning'
        msg = "Aucun établissement ne semble porter ce nom."
    elif(response.status_code == 500):
        status = 'warning'
        msg = "Le serveur est momentanément indisponible. Veuillez réessayer ultérieurement."
    elif(response.status_code == 429):
        status = 'warning'
        msg = "La volumétrie d'appel a été dépassée (maximum 7 appels/seconde). Votre IP risque d'être blacklistée"
    else:
        status = 'error'
        msg = "An unexpected error occured"

    return {
        'status': status,
        'msg': msg,
        'data': data
    }