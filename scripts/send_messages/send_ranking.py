import os
from scripts.utils import api_google as ag
from scripts.utils import api_whatsapp as aw

SHEET_ID = os.environ['SHEET_ID']
gc       = ag.autenticar_sheets()

usuarios          = ag.ler_planiha_df(gc, 'usuarios', SHEET_ID)
parcial_usuario   = ag.ler_planiha_df(gc, 'parcial_usuario', SHEET_ID)
mensagem_ranking  = aw.montar_mensagem_ranking(parcial_usuario, usuarios)

if mensagem_ranking is not None:
    aw.enviar_mensagem_ranking(mensagem_ranking)