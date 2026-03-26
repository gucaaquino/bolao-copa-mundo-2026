import os
from scripts.utils import api_google as ag

SHEET_ID         = os.environ['SHEET_ID']
SHEET_ID_APOSTAS = os.environ['SHEET_ID_APOSTAS']
gc               = ag.autenticar_sheets()

def atualizar():
    apostas_inseridas = ag.ler_planiha_df(gc, 'apostas', SHEET_ID_APOSTAS)
    ag.montar_planilha_apostas(gc, apostas_inseridas, SHEET_ID)
    ag.montar_planilha_usuarios(gc, apostas_inseridas, SHEET_ID)

if __name__ == '__main__':
    atualizar()