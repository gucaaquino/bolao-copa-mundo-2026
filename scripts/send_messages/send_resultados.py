import os
from scripts.utils import api_google as ag
from scripts.utils import api_whatsapp as aw

SHEET_ID                   = os.environ['SHEET_ID']
gc                         = ag.autenticar_sheets()
EVOLUTION_PHONE_RESULTADOS = os.environ['EVOLUTION_PHONE_RESULTADOS']

# resultados          = ag.ler_planiha_df(gc, 'resultados', SHEET_ID)
# times               = ag.ler_planiha_df(gc, 'times', SHEET_ID)
# jogos               = ag.ler_planiha_df(gc, 'jogos', SHEET_ID)
# mensagem_resultados = aw.montar_mensagem_resultados(resultados, jogos, times)

# if mensagem_resultados is not None:
    # aw.enviar_whatsapp(mensagem_resultados, EVOLUTION_PHONE_RESULTADOS)

aw.enviar_whatsapp('seu ze mane', '5519971656937')