import random
import pandas as pd
import pytz
from datetime import datetime
import os
import requests

BR_TZ                       = pytz.timezone('America/Sao_Paulo')
EVOLUTION_URL               = os.environ['EVOLUTION_URL']
EVOLUTION_APIKEY            = os.environ['EVOLUTION_APIKEY']
EVOLUTION_PHONE_ANUNCIOS    = os.environ['EVOLUTION_PHONE_ANUNCIOS']
EVOLUTION_PHONE_RESULTADOS  = os.environ['EVOLUTION_PHONE_RESULTADOS']

saudacoes = [
    "Fala meu jogador",
    "Fala galera",
    "Salve time",
    "E aí pessoal",
    "Boa galera",
    "Fala tropa",
    "E aí jogadores",
]

introducoes_resultados = [
    "aqui vão os resultados parciais:",
    "confere os resultados até agora:",
    "olha como estamos até o momento:",
    "segue o placar parcial:",
    "bora ver como tá ficando:",
]

complementos = [
    "",
    " 🔥",
    " 👀",
    " 📊",
    " 🚀",
]

def montar_mensagem_bom_dia(df_jogos: pd.DataFrame, df_times: pd.DataFrame):
    current_date = datetime.now(BR_TZ).strftime('%d/%m/%Y')

    jogos_hoje = df_jogos[df_jogos['data'] == current_date].copy()

    mensagem = f'*{random.choice(saudacoes)}, muito bom dia!*'

    if not jogos_hoje.empty:

        mapa_times = dict(zip(df_times['sigla'], df_times['nome']))

        jogos_hoje['time_casa'] = jogos_hoje['sigla_casa'].map(mapa_times)
        jogos_hoje['time_fora'] = jogos_hoje['sigla_fora'].map(mapa_times)

        jogos_hoje = jogos_hoje.sort_values(by=['grupo', 'hora'])

        mensagem += f'\nHoje teremos jogo(s) importante(s)! Segue a lista{random.choice(complementos)}:'

        for grupo, df_grupo in jogos_hoje.groupby('grupo'):
            mensagem += f'\n*Grupo {grupo}:*'

            for _, j in df_grupo.iterrows():
                casa = j['time_casa'] if pd.notna(j['time_casa']) else j['sigla_casa']
                fora = j['time_fora'] if pd.notna(j['time_fora']) else j['sigla_fora']

                mensagem += f"\n - {j['hora']} | {casa} x {fora}"
    else:
        mensagem += '\nHoje infelizmente não temos nenhum jogo programado!'

    return mensagem

def montar_mensagem_resultados(df_resultados, df_times):

    current_date = datetime.now(BR_TZ).strftime('%d/%m/%Y')

    resultados_hoje = df_resultados[df_resultados['data'] == current_date].copy()

    if resultados_hoje.empty:
        return 'Hoje não há jogos acontecendo.'

    resultados_hoje['gols_casa'] = pd.to_numeric(resultados_hoje['gols_casa'], errors='coerce')
    resultados_hoje['gols_fora'] = pd.to_numeric(resultados_hoje['gols_fora'], errors='coerce')

    mapa_times = dict(zip(df_times['sigla'], df_times['nome']))

    resultados_hoje['time_casa'] = resultados_hoje['sigla_casa'].map(mapa_times)
    resultados_hoje['time_fora'] = resultados_hoje['sigla_fora'].map(mapa_times)

    resultados_hoje = resultados_hoje.sort_values(by=['grupo', 'hora'])

    mensagem = '📊 *Resultados dos jogos de hoje:*'

    for grupo, df_grupo in resultados_hoje.groupby('grupo'):
        mensagem += f'\n\n*Grupo {grupo}:*'

        for _, j in df_grupo.iterrows():

            if pd.notna(j['gols_casa']) and pd.notna(j['gols_fora']):
                placar = f"{int(j['gols_casa'])} x {int(j['gols_fora'])}"
            else:
                placar = "x"

            casa = j['time_casa'] if pd.notna(j['time_casa']) else j['sigla_casa']
            fora = j['time_fora'] if pd.notna(j['time_fora']) else j['sigla_fora']

            mensagem += f"\n - {j['hora']} | {casa} {placar} {fora}"

    return mensagem

def enviar_whatsapp(mensagem, EVOLUTION_PHONE):
    url     = f'{EVOLUTION_URL}/message/sendText/vm-bolao-copa'
    headers = {
        'apikey': EVOLUTION_APIKEY,
        'Content-Type': 'application/json'
    }
    payload = {
        'number': EVOLUTION_PHONE,
        'text': mensagem
    }
    r = requests.post(url, json=payload, headers=headers)
    if r.status_code == 201:
        print('✅ Mensagem enviada no WhatsApp!')
    else:
        raise Exception(f'Erro ao enviar: {r.text}')
    
def enviar_mensagem_anuncio(mensagem):
    enviar_whatsapp(mensagem, EVOLUTION_PHONE_ANUNCIOS)
    
def enviar_mensagem_resultado(mensagem):
    enviar_whatsapp(mensagem, EVOLUTION_PHONE_RESULTADOS)