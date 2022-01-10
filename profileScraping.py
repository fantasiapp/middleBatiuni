import requests
import csv

from decorators import *
import os
import sys


NAF_classe_dict = {}
NAF_sous_classe_dict = {}

package_directory = os.path.dirname(os.path.abspath(__file__))
sys.path.append('/var/fantasiapp/batiUni/middle/')

from bdd import executeRequest

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
@timer
def searchUnitesLegalesByDenomination(denomination: str) -> dict:
    '''
        Recherche les unités légales qui s'écrivent exactement avec cette dénomination (à la normalisation près)
        Retour sous la forme d'un dictionnaire avec une clé "error" ou "unites_legales" selon le succès de la requête
    '''
    status, msg, data = "error", "An unexpected error occured", None
    denomination_formatted = str(denomination).upper()
    
    try:
        resList = executeRequest(f'SELECT siren, activitePrincipaleUniteLegale, nicSiegeUniteLegale FROM unites_legales WHERE denominationUniteLegale LIKE "{denomination_formatted}" LIMIT 10', dml=True)
        print(resList)
        if not resList:
            status = "info"
            msg = "Aucun établissement ne semble porter ce nom."
        elif len(resList) == 1:
            status="OK"
            msg="Oll Korrekt"
            nic_siege = resList[0][2]
            siege = executeRequest(f'SELECT numeroVoieEtablissement, typeVoieEtablissement, libelleVoieEtablissement, codePostalEtablissement, libelleCommuneEtablissement FROM etablissements WHERE siren LIKE "{denomination_formatted} AND nic LIKE {nic_siege}" LIMIT 10', dml=True)
            data = {
                    'denomination': denomination,
                    'siren': resList[0][0],
                    'code_activite_principale' : resList[0][1],
                    'libelle_activite_principale': NAF_classe_dict[resList[0][1]] or NAF_sous_classe_dict[resList[0][1]] or "Activité inconnue",
                    'tva': f'FR{(12+3*(resList[0][0]%97))%97}{resList[0][0]}'
                    }
            if siege:
                siege = siege[0]
                data['adresse'] = f'{siege[0]} {siege[1]} {siege[2]}, {siege[3]} {siege[4]}'
        else:
            status="info"
            msg=f'Pas assez d\'informations. {len(resList)} matchs trouvés'

    except:
        print("Something wrong happened ...")

    return {
        'status': status,
        'msg': msg,
        'data': data
    }
