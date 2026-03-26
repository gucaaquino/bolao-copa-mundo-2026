import os
from scripts.utils import api_google as ag
from scripts.utils import api_whatsapp as aw

SHEET_ID = os.environ['SHEET_ID']
gc       = ag.autenticar_sheets()

jogos = ag.ler_planiha_df(gc, 'jogos', SHEET_ID)
times = ag.ler_planiha_df(gc, 'times', SHEET_ID)

bom_dia = aw.montar_mensagem_bom_dia(jogos, times)

aw.enviar_mensagem_anuncio(bom_dia)