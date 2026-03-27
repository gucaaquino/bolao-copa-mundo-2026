import random
import pandas as pd
import pytz
from datetime import datetime
import os
import requests

BR_TZ = pytz.timezone('America/Sao_Paulo')

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


def enviar_whatsapp(mensagem, EVOLUTION_PHONE):
    EVOLUTION_URL    = os.environ['EVOLUTION_URL']
    EVOLUTION_APIKEY = os.environ['EVOLUTION_APIKEY']

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
    
def montar_mensagem_bom_dia(df_jogos: pd.DataFrame, df_times: pd.DataFrame):
    current_date = datetime.now(BR_TZ).strftime('%d/%m/%Y')

    jogos_hoje = df_jogos[df_jogos['data'] == current_date].copy()

    mensagem = f'*{random.choice(saudacoes)}, muito bom dia!*'

    if not jogos_hoje.empty:

        mapa_times = dict(zip(df_times['id'], df_times['nome']))

        jogos_hoje['time_casa'] = jogos_hoje['id_time_casa'].map(mapa_times)
        jogos_hoje['time_fora'] = jogos_hoje['id_time_fora'].map(mapa_times)

        jogos_hoje = jogos_hoje.sort_values(by=['grupo', 'hora'])

        mensagem += f'\nHoje teremos jogo(s) importante(s)! Segue a lista{random.choice(complementos)}:'

        for grupo, df_grupo in jogos_hoje.groupby('grupo'):
            mensagem += f'\n*Grupo {grupo}:*'

            for _, j in df_grupo.iterrows():
                casa = j['time_casa'] if pd.notna(j['time_casa']) else j['id_time_casa']
                fora = j['time_fora'] if pd.notna(j['time_fora']) else j['id_time_fora']

                mensagem += f'\n - {j["hora"]} | {casa} x {fora}'
    else:
        mensagem += '\nHoje infelizmente não temos nenhum jogo programado!'

    return mensagem

def montar_mensagem_resultados(df_resultados, df_jogos, df_times):

    current_dt = datetime.now(BR_TZ)
    current_date = current_dt.strftime('%d/%m/%Y')
    hora_execucao = current_dt.strftime('%H:%M')

    jogos_hoje = df_jogos[df_jogos['data'] == current_date].copy()

    if jogos_hoje.empty:
        return None

    mapa_times_id_to_name = dict(zip(df_times['id'], df_times['nome']))

    jogos_hoje['time_casa'] = jogos_hoje['id_time_casa'].map(mapa_times_id_to_name)
    jogos_hoje['time_fora'] = jogos_hoje['id_time_fora'].map(mapa_times_id_to_name)
    jogos_hoje = jogos_hoje.rename(columns={'id': 'id_jogo'}).copy()

    df_resultados['gols_casa'] = pd.to_numeric(df_resultados['gols_casa'], errors='coerce')
    df_resultados['gols_fora'] = pd.to_numeric(df_resultados['gols_fora'], errors='coerce')

    resultados_hoje = jogos_hoje.merge(
        df_resultados[['id_jogo', 'gols_casa', 'gols_fora', 'status']],
        on='id_jogo',
        how='left',
        suffixes=('_jogos', '_resultados')
    )

    resultados_hoje = resultados_hoje.sort_values(by=['grupo', 'hora'])

    mensagem = '📊 *Resultados dos jogos de hoje:*'

    for grupo, df_grupo in resultados_hoje.groupby('grupo'):
        mensagem += f'\n\n*Grupo {grupo}:*'

        for _, j in df_grupo.iterrows():
            placar = 'x'
            status = ''
            if j['status'] == 'encerrado' or j['status'] == 'em_andamento':
                if pd.notna(j['gols_casa']) and pd.notna(j['gols_fora']):
                    if j['status'] == 'encerrado':
                        status = ' ✅'
                    else:
                        status = ' 🔴'

                    placar = f'{int(j["gols_casa"])} x {int(j["gols_fora"])}'
            elif j['status'] == 'futuro':
                placar = 'x' 

            casa = j['time_casa'] if pd.notna(j['time_casa']) else 'Time Casa Desconhecido'
            fora = j['time_fora'] if pd.notna(j['time_fora']) else 'Time Fora Desconhecido'

            mensagem += f'\n - {j["hora"]} | {casa} {placar} {fora}{status}'

    mensagem += '\n\nLegenda:'
    mensagem += '\n✅ Jogo computado'
    mensagem += '\n🔴 Jogo sendo computado'
    mensagem += f'\n\n🕒 Atualizado às {hora_execucao}'

    return mensagem

def montar_mensagem_ranking(df_parcial, df_usuarios):

    current_dt = datetime.now(BR_TZ)
    hora_execucao = current_dt.strftime('%H:%M')

    if df_parcial.empty:
        return None

    df = df_parcial.copy()

    df = df.merge(df_usuarios, on='email', how='left')
    df['nome'] = df['nome'].fillna(df['email'])

    df = df.sort_values('total', ascending=False).reset_index(drop=True)

    df['posicao'] = range(1, len(df) + 1)

    menor_pontuacao = df['total'].min()

    mensagem = '🏆 *Ranking Geral do Bolão:*\n'

    for _, row in df.iterrows():
        medalha = ''
        if row['posicao'] == 1:
            medalha = '🥇 '
        elif row['posicao'] == 2:
            medalha = '🥈 '
        elif row['posicao'] == 3:
            medalha = '🥉 '

        lanterna = ' 🔦' if row['total'] == menor_pontuacao else ''

        mensagem += (
            f"\n{medalha}{row['posicao']}º - {row['alias']} "
            f"({int(row['total'])} pts){lanterna}"
        )
    
    mensagem += f"\n\n🕒 Atualizado às {hora_execucao}"

    return mensagem