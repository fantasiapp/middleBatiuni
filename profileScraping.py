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
# @timer
# def searchUnitesLegalesByDenomination(denomination: str) -> dict:
#     '''
#         Recherche les unités légales qui s'écrivent exactement avec cette dénomination (à la normalisation près)
#         Retour sous la forme d'un dictionnaire avec une clé "error" ou "unites_legales" selon le succès de la requête
#     '''
#     status, msg, data = "error", "An unexpected error occured", None
#     denomination_formatted = str(denomination).upper()
   
#     try:
#         resList = executeRequest(f'SELECT siren, activitePrincipaleUniteLegale, nicSiegeUniteLegale FROM unites_legales WHERE denominationUniteLegale LIKE "{denomination_formatted}" LIMIT 10', dml=True)
#         print(resList)
#         if not resList:
#             status = "info"
#             msg = "Aucun établissement ne semble porter ce nom."
#         elif len(resList) == 1:
#             status="OK"
#             msg="Oll Korrekt"
            
#             siren=resList[0][0]
#             nic_siege = resList[0][2]
#             cle_tva = (12+(3*int(siren)%97))%97
#             siege = executeRequest(f'SELECT numeroVoieEtablissement, typeVoieEtablissement, libelleVoieEtablissement, codePostalEtablissement, libelleCommuneEtablissement FROM etablissements WHERE siren LIKE "{siren}" AND nic LIKE "{nic_siege}" LIMIT 10', dml=True)
#             data = {
#                     'denomination': denomination,
#                     'siren': siren,
#                     'code_activite_principale' : resList[0][1],
#                     'libelle_activite_principale': getSousClasseByNAF(resList[0][1]) or getClasseByNAF(resList[0][1]) or "Activité inconnue",
#                     'tva': f'FR{cle_tva}{resList[0][0]}'
#                     }
#             if siege:
#                 print(siege)
#                 siege = siege[0]
#                 data['adresse'] = f'{siege[0]} {siege[1]} {siege[2]}, {siege[3]} {siege[4]}'
#         else:
#             status="info"
#             msg=f'Pas assez d\'informations. {len(resList)} matchs trouvés'

#     except:
#         print("Something wrong happened ...")

#     return {
#         'status': status,
#         'msg': msg,
#         'data': data
#     }

@timer
def searchUnitesLegalesByDenomination(denomination: str) -> list[dict]:
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
            msg = "Aucune unité légale ne semble porter ce nom."
        else:
            status="OK"
            msg="Oll Korrekt"
            data = []
            for res in resList:
                siren=res[0]
                nic_siege = res[2]
                cle_tva = (12+(3*int(siren)%97))%97
                siege = executeRequest(f'SELECT numeroVoieEtablissement, typeVoieEtablissement, libelleVoieEtablissement, codePostalEtablissement, libelleCommuneEtablissement FROM etablissements WHERE siren LIKE "{siren}" AND nic LIKE "{nic_siege}" LIMIT 1', dml=True)
                nbEtablissements = executeRequest(f'SELECT COUNT(siret) FROM etablissements WHERE siren LIKE "{siren}"', dml=True)[0][0]
                unite_legale = {
                        'denomination': denomination,
                        'siren': siren,
                        'code_activite_principale' : res[1],
                        'libelle_activite_principale': getSousClasseByNAF(res[1]) or getClasseByNAF(res[1]) or "Activité inconnue",
                        'tva': f'FR{cle_tva}{res[0]}',
                        'nbEtablissements': nbEtablissements
                        }
                if siege:
                    siege = siege[0]
                    unite_legale['adresse'] = f'{siege[0]} {siege[1]} {siege[2]}, {siege[3]} {siege[4]}'

                data.append(unite_legale)

    except:
        print("Something wrong happened ...")
    return {
        'status': status,
        'msg': msg,
        'data': data
    }

def searchEtablissementBySiren(siren: str) ->list[dict]:
    status, msg, data = "error", "An unexpected error occured", None

    try:
        resList = executeRequest(f'SELECT siret, nic, activitePrincipaleEtablissement, numeroVoieEtablissement, typeVoieEtablissement, libelleVoieEtablissement, codePostalEtablissement, libelleCommuneEtablissement FROM etablissements WHERE siren LIKE "{siren}"', dml=True)
        data = []
        if not resList:
            status = "info"
            msg = "Aucun établissement ne semble porter ce nom."
        else:
            status="OK"
            msg="Oll Korrekt"
            for res in resList:
                etablissement = {
                    'siret': res[0],
                    'nic': res[1],
                    'code_activite_principale': res[2],
                    'libelle_activite_principale': getSousClasseByNAF(res[2]) or getClasseByNAF(res[2]) or "Activité inconnue",
                    'adresse': f'{res[3]} {res[4]} {res[5]}, {res[6]} {res[7]}'
                }
            data.append(etablissement)
    except:
        print("Something wrong happened ...")
    return {
        'status': status,
        'msg': msg,
        'data': data
    }