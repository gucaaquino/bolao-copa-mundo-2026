import os
import json
from scripts.utils import api_google as ag
from scripts.utils import api_footballorg as af

SHEET_ID    = os.environ['SHEET_ID']
RODADAS     = json.loads(os.environ['RODADAS'])
API_TOKEN   = os.environ['FOOTBALL_API_TOKEN']
COMPETICAO  = os.environ['COMPETICAO'] 
gc          = ag.autenticar_sheets()

def atualizar():
    jogos_api = af.buscar_jogos_api(RODADAS, API_TOKEN, COMPETICAO)
    times_api = af.buscar_times_api(API_TOKEN, COMPETICAO)

    ag.montar_planilha_jogos(gc, jogos_api, SHEET_ID)
    ag.montar_planilha_times(gc, times_api, SHEET_ID)

if __name__ == '__main__':
    atualizar()