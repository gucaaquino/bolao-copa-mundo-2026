import os
from scripts.utils import api_google as ag
from scripts.utils import api_whatsapp as aw

SHEET_ID = os.environ['SHEET_ID']
gc       = ag.autenticar_sheets()

resultados          = ag.ler_planiha_df(gc, 'resultados', SHEET_ID)
times               = ag.ler_planiha_df(gc, 'times', SHEET_ID)
mensagem_resultados = aw.montar_mensagem_resultados(resultados, times)

if mensagem_resultados is not None:
    aw.enviar_mensagem_resultado(mensagem_resultados)