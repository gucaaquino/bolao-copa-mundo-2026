from scripts.planilhas_google_utils import *
from scripts.api_whatsapp_utils import *

gc = autenticar_sheets()

resultados = ler_planiha(gc, 'resultados')
times = ler_planiha(gc, 'times')

bom_dia = montar_mensagem_resultados(resultados, times)

enviar_mensagem_resultado(bom_dia)