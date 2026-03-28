import os
from scripts.utils import api_google as ag

SHEET_ID = os.environ['SHEET_ID']
gc       = ag.autenticar_sheets()

def atualizar():
    apostas    = ag.ler_planiha_df(gc, 'apostas', SHEET_ID)
    pontuacao  = ag.ler_planiha_df(gc, 'pontuacao', SHEET_ID)
    resultados = ag.ler_planiha_df(gc, 'resultados', SHEET_ID)
    jogos      = ag.ler_planiha_df(gc, 'jogos', SHEET_ID)

    ag.montar_planilha_pontuacao_usuario(gc, apostas, resultados, pontuacao, SHEET_ID)
    pontuacao_usuario = ag.ler_planiha_df(gc, 'pontuacao_usuario', SHEET_ID)

    ag.montar_planilha_parcial_usuario(gc, pontuacao_usuario, jogos, SHEET_ID)

if __name__ == '__main__':
    atualizar()