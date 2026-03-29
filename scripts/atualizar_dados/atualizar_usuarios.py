import os
from scripts.utils import api_google as ag

SHEET_ID = os.environ['SHEET_ID']
gc       = ag.autenticar_sheets()

def atualizar():
    palpites = ag.ler_planiha_df(gc, 'palpites', SHEET_ID)
    ag.montar_planilha_usuarios(gc, palpites, SHEET_ID)

if __name__ == '__main__':
    atualizar()