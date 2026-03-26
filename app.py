from scripts.api_dados_futebol_utils import *
from scripts.planilhas_google_utils import *
from scripts.api_whatsapp_utils import *

gc = autenticar_sheets()
# jogos_api = buscar_jogos_api([9])
# montar_planilha_resultados(gc, jogos_api)
# montar_planilha_jogos(gc, jogos_api)

# times_api = buscar_times_api()
# montar_planilha_times(gc, times_api)

jogos = ler_planiha(gc, 'jogos')
resultados = ler_planiha(gc, 'resultados')
times = ler_planiha(gc, 'times')