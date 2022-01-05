import requests
import csv

NAF_classe_dict = {}
NAF_sous_classe_dict = {}

reader = csv.reader(open('./assets/naf2008-liste-n4-classes.csv', 'r', encoding='UTF-8'))
for row in reader:
   k, v = row
   NAF_classe_dict[k] = v

reader = csv.reader(open('./assets/naf2008-liste-n5-sous-classes.csv', 'r', encoding='UTF-8'))
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

    def getFields() -> list[str]:
        return LegalUnit.fields

def searchUnitesLegalesByDenomination(denomination: str) -> dict:
    '''
        Recherche les unités légales qui s'écrivent exactement avec cette dénomination (à la normalisation près)
        Retour sous la forme d'un dictionnaire avec une clé "error" ou "unites_legales" selon le succès de la requête
    '''
    res = {}
    denomination = str(denomination).upper()
    
    params = { 
        'action': 'query', 
        'format': 'json',
        'denomination': denomination,
        'prop': 'extracts', 
        'explaintext': True
    }

    response = requests.get(
         'https://entreprise.data.gouv.fr/api/sirene/v3/unites_legales',
         params= params
    )
    if(response.status_code == 200):
        results = response.json()
        res['unites_legales'] = [LegalUnit.extractFields(data) for data in results['unites_legales']]

    elif(response.status_code == 404):
        res['error'] = "Aucun établissement ne semble porter ce nom."
    elif(response.status_code == 500):
        res['error'] = "Le serveur est momentanément indisponible. Veuillez réessayer ultérieurement."
    elif(response.status_code == 429):
        res['error'] = "La volumétrie d'appel a été dépassée (maximum 7 appels/seconde). Votre IP risque d'être blacklistée"
    else:
        res['error'] = "Une erreur non-traitée est survenue"
    
    return res