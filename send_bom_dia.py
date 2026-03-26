from scripts.planilhas_google_utils import *
from scripts.api_whatsapp_utils import *

gc = autenticar_sheets()

jogos = ler_planiha(gc, 'jogos')
times = ler_planiha(gc, 'times')

bom_dia = montar_mensagem_bom_dia(jogos, times)

enviar_mensagem_anuncio(bom_dia)