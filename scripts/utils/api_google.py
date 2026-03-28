import pandas as pd
import json
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import pytz
import random
import os

BR_TZ = pytz.timezone('America/Sao_Paulo')

def autenticar_sheets():
    if os.getenv("GOOGLE_CREDENTIALS"):
        CREDENTIALS = json.loads(os.environ['GOOGLE_CREDENTIALS'])
        SCOPES      = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']

        creds = Credentials.from_service_account_info(CREDENTIALS, scopes=SCOPES)
    else:
        creds = Credentials.from_service_account_file(
            "creds/google-key.json",
            scopes=["https://www.googleapis.com/auth/spreadsheets"]
        )

    return gspread.authorize(creds)

def formatar_data_hora(utc_str):
    if not utc_str:
        return '-', '-'
    dt = datetime.fromisoformat(utc_str.replace('Z', '+00:00'))
    dt_br = dt.astimezone(BR_TZ)
    return dt_br.strftime('%d/%m/%Y'), dt_br.strftime('%H:%M')

def traduzir_status(status):
    mapa = {
        'SCHEDULED':        'futuro',
        'TIMED':            'futuro',
        'IN_PLAY':          'em_andamento',
        'PAUSED':           'em_andamento',
        'FINISHED':         'encerrado',
        'EXTRA_TIME':       'em_andamento',
        'PENALTY_SHOOTOUT': 'em_andamento',
        'SUSPENDED':        'futuro',
        'POSTPONED':        'futuro',
        'CANCELLED':        'futuro',
        'AWARDED':          'encerrado'
    }

    return mapa.get(status, status)

def montar_planilha_jogos(gc, jogos, SHEET_ID):
    nome_aba  = 'jogos'
    cabecalho = ['id', 'data', 'hora', 'id_time_casa', 'id_time_fora', 'grupo']
    dados     = [cabecalho]

    for p in jogos:
        id         = p.get('id')
        data, hora = formatar_data_hora(p.get('utcDate'))
        id_casa = p['homeTeam'].get('id')
        id_fora = p['awayTeam'].get('id')

        grupo = random.choice(['A', 'B'])
        data = datetime.now(BR_TZ).strftime('%d/%m/%Y')

        dados.append([id, data, hora, id_casa, id_fora, grupo])

    preencher_planilha(gc, nome_aba, dados, SHEET_ID)

def montar_planilha_resultados(gc, jogos, SHEET_ID):
    nome_aba  = 'resultados'
    cabecalho = ['id_jogo', 'status', 'gols_casa', 'gols_fora']
    dados     = [cabecalho]

    for p in jogos:
        id           = p.get('id')
        status       = random.choice(['futuro', 'encerrado', 'em_andamento'])#traduzir_status(p.get('status'))
        gols_casa    = p['score']['fullTime']['home']
        gols_fora    = p['score']['fullTime']['away']

        dados.append([id, status, str(gols_casa) if gols_casa is not None else '', str(gols_fora) if gols_fora is not None else ''])
      
    preencher_planilha(gc, nome_aba, dados, SHEET_ID)

def montar_planilha_times(gc, times, SHEET_ID):
    nome_aba  = 'times'
    cabecalho = ['id', 'nome', 'sigla']
    dados = [cabecalho]

    for t in times:
        dados.append(t)

    preencher_planilha(gc, nome_aba, dados, SHEET_ID)

def montar_planilha_apostas(gc, apostas, jogos, times, SHEET_ID):
    mapa_times = dict(zip(times['id'], times['sigla']))

    jogos_hoje = jogos.copy()
    jogos_hoje['time_casa'] = jogos_hoje['id_time_casa'].map(mapa_times)
    jogos_hoje['time_fora'] = jogos_hoje['id_time_fora'].map(mapa_times)

    de_para = {}
    de_para['Endereço de e-mail'] = 'email'
    de_para['Nome completo']      = 'nome'
    de_para['Número de Telefone'] = 'numero'

    for _, j in jogos_hoje.iterrows():
        if j['id_time_casa'] == 4241:
            j['time_casa'] = 'CFC'
        if j['id_time_fora'] == 4241:
            j['time_fora'] = 'CFC'
        if j['id_time_casa'] == 1776:
            j['time_casa'] = 'SAO'
        if j['id_time_fora'] == 1776:
            j['time_fora'] = 'SAO'
        de_para[f'{j["time_casa"]} x {j["time_fora"]} - Gols Casa'] = f'{j["id"]}C'
        de_para[f'{j["time_casa"]} x {j["time_fora"]} - Gols Fora'] = f'{j["id"]}F'

    apostas = apostas.rename(columns=de_para).drop(columns=['Carimbo de data/hora'])

    apostas_unpivot = apostas.melt(
        id_vars=['email', 'numero'],
        var_name='jogo',
        value_name='resultado'
    )

    apostas_unpivot[['id_jogo', 'sigla']] = apostas_unpivot['jogo'].str.extract('(^\d+)([CF]$)')

    apostas_pivot = apostas_unpivot.pivot_table(
        index=['email', 'id_jogo'],
        columns='sigla',
        values='resultado'
    ).reset_index()

    apostas_pivot.columns.name = None
    apostas_pivot = apostas_pivot.rename(columns={
        'C': 'gols_casa',
        'F': 'gols_fora'
    })

    preencher_planilha_df(gc, 'apostas', apostas_pivot, SHEET_ID)

def montar_planilha_usuarios(gc, apostas, SHEET_ID):
    de_para = {}
    de_para['Endereço de e-mail'] = 'email'
    de_para['Nome completo']      = 'nome'
    de_para['Número de Telefone'] = 'numero'
    apostas = apostas.rename(columns=de_para)

    usuarios = apostas[['email', 'nome', 'numero']].drop_duplicates()
    usuarios['alias'] = usuarios['nome'].apply(lambda x: f'{x.split()[0]} {x.split()[-1]}' if len(x.split()) > 1 else x)

    preencher_planilha_df(gc, 'usuarios', usuarios, SHEET_ID)

def montar_planilha_pontuacao_usuario(gc, apostas, resultados, pontuacao, SHEET_ID):
    resultados_enc = resultados[resultados['status'] == 'encerrado'].copy()
    df = apostas.merge(
        resultados_enc,
        on='id_jogo',
        how='inner',
        suffixes=('_palpite', '_real')
    )

    df = df.rename(columns={
        'gols_casa_palpite': 'palpite_casa',
        'gols_fora_palpite': 'palpite_fora',
        'gols_casa_real': 'gols_casa',
        'gols_fora_real': 'gols_fora'
    })

    def classificar(row):
        pc, pf = row['palpite_casa'], row['palpite_fora']
        rc, rf = row['gols_casa'], row['gols_fora']

        # Placar exato
        if pc == rc and pf == rf:
            return 'placar'

        # Empate
        if rc == rf and pc == pf:
            return 'empate'

        # Vencedor correto
        if (rc > rf and pc > pf) or (rc < rf and pc < pf):
            return 'vencedor'

        return 'erro'

    df['resultado_aposta'] = df.apply(classificar, axis=1)

    mapa_pontos = dict(zip(pontuacao['resultado'], pontuacao['pontos']))

    df['pontos'] = df['resultado_aposta'].map(mapa_pontos).fillna(0)

    df_final = df[[
        'email',
        'id_jogo',
        'gols_casa',
        'gols_fora',
        'palpite_casa',
        'palpite_fora',
        'pontos'
    ]].copy()

    preencher_planilha_df(gc, 'pontuacao_usuario', df_final, SHEET_ID)

def montar_planilha_parcial_usuario(gc, pontuacao_usuario, jogos, SHEET_ID):

    if pontuacao_usuario.empty:
        preencher_planilha(gc, 'parcial_usuario', [['email', 'total']], SHEET_ID)
        return None

    mapa_grupos = dict(zip(jogos['id'], jogos['grupo']))
    pontuacao_usuario['grupo'] = pontuacao_usuario['id_jogo'].map(mapa_grupos)

    df_grupo = (
        pontuacao_usuario.groupby(['email', 'grupo'])['pontos']
        .sum()
        .reset_index()
    )

    df_pivot = df_grupo.pivot(
        index='email',
        columns='grupo',
        values='pontos'
    ).fillna(0)

    df_pivot.columns = [f'grupo_{g}' for g in df_pivot.columns]

    df_pivot['total'] = df_pivot.sum(axis=1)

    df_final = df_pivot.reset_index()

    preencher_planilha_df(gc, 'parcial_usuario', df_final, SHEET_ID)

def preencher_planilha(gc, nome_aba, dados, SHEET_ID):
    sh = gc.open_by_key(SHEET_ID)

    try:
        aba = sh.worksheet(nome_aba)
        aba.clear()
        print(f'🔄 Aba "{nome_aba}" limpa')
    except gspread.exceptions.WorksheetNotFound:
        aba = sh.add_worksheet(title=nome_aba, rows=20, cols=8)
        print(f'✨ Aba "{nome_aba}" criada')

    aba.update(dados, 'A1')
    print(f'✅ Planilha atualizada com {len(dados)} linhas!')

def preencher_planilha_df(gc, nome_aba, df, SHEET_ID):
    dados = [df.columns.tolist()] + df.fillna("").values.tolist()

    preencher_planilha(gc, nome_aba, dados, SHEET_ID)

def ler_planiha_df(gc, nome_aba, SHEET_ID):
    sh = gc.open_by_key(SHEET_ID)
    abas = [a.title for a in sh.worksheets() if a.title == nome_aba]

    if len(abas) < 1:
        print(f'❌ Nenhuma aba {nome_aba} encontrada.')
        return None
        
    print(f'📋 Lendo aba: {nome_aba}')

    aba = sh.worksheet(nome_aba)
    dados = aba.get_all_records()

    return pd.DataFrame(dados)