import os
from scripts.utils import api_google as ag
from scripts.utils import api_footballorg as af

SHEET_ID  = os.environ['SHEET_ID']
API_TOKEN = os.environ['FOOTBALL_API_TOKEN']
gc        = ag.autenticar_sheets()

def atualizar():
    # busca resultados
    jogos_api = af.buscar_jogos_api([9], API_TOKEN)

    ag.montar_planilha_resultados(gc, jogos_api, SHEET_ID)

if __name__ == '__main__':
    atualizar()