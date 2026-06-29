import os
import json
from scripts.utils import api_google as ag
from scripts.utils import api_footballorg as af

SHEET_ID   = os.environ['SHEET_ID']
API_TOKEN  = os.environ['FOOTBALL_API_TOKEN']
COMPETICAO = os.environ['COMPETICAO']
gc         = ag.autenticar_sheets()

def atualizar():
    jogos     = ag.ler_planiha_df(gc, 'jogos', SHEET_ID)
    jogos_api = af.buscar_jogos_api(jogos['id'].tolist(), API_TOKEN, COMPETICAO)

    ag.montar_planilha_resultados(gc, jogos_api, SHEET_ID)

if __name__ == '__main__':
    atualizar()