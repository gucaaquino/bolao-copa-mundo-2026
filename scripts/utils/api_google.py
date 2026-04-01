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
        id_casa    = p['homeTeam'].get('id')
        id_fora    = p['awayTeam'].get('id')

        grupo = random.choice(['A', 'B'])

        dados.append([id, data, hora, id_casa, id_fora, grupo])

    preencher_planilha(gc, nome_aba, dados, SHEET_ID)

def montar_planilha_resultados(gc, jogos, SHEET_ID):
    nome_aba  = 'resultados'
    cabecalho = ['jogo_id', 'status', 'gol_casa', 'gol_fora']
    dados     = [cabecalho]

    for p in jogos:
        id       = p.get('id')
        status   = traduzir_status(p.get('status'))
        gol_casa = p['score']['fullTime']['home']
        gol_fora = p['score']['fullTime']['away']

        dados.append([id, status, str(gol_casa) if gol_casa is not None else '', str(gol_fora) if gol_fora is not None else ''])

    preencher_planilha(gc, nome_aba, dados, SHEET_ID)

def montar_planilha_times(gc, times, SHEET_ID):
    nome_aba  = 'times'
    cabecalho = ['id', 'nome', 'sigla']
    dados = [cabecalho]

    for t in times:
        dados.append(t)

    preencher_planilha(gc, nome_aba, dados, SHEET_ID)

def montar_planilha_usuarios(gc, apostas, SHEET_ID):

    usuarios = apostas[['email', 'nome', 'telefone']].drop_duplicates().copy()
    usuarios['alias'] = usuarios['nome'].apply(lambda x: f'{x.split()[0]} {x.split()[-1]}' if len(x.split()) > 1 else x)

    preencher_planilha_df(gc, 'usuarios', usuarios, SHEET_ID)

def montar_planilha_pontuacao_usuario(gc, apostas, resultados, pontuacao, SHEET_ID):
    resultados_enc = resultados[~(resultados['status'] == 'futuro')].copy()
    df = apostas.merge(
        resultados_enc,
        on='jogo_id',
        how='inner',
        suffixes=('_palpite', '_real')
    )

    df = df.rename(columns={
        'gol_casa_palpite': 'palpite_casa',
        'gol_fora_palpite': 'palpite_fora',
        'gol_casa_real': 'gol_casa',
        'gol_fora_real': 'gol_fora'
    })

    def classificar(row):
        pc, pf = row['palpite_casa'], row['palpite_fora']
        rc, rf = row['gol_casa'], row['gol_fora']

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
        'jogo_id',
        'gol_casa',
        'gol_fora',
        'palpite_casa',
        'palpite_fora',
        'pontos'
    ]].copy()

    preencher_planilha_df(gc, 'pontuacao_usuario', df_final, SHEET_ID)

def montar_planilha_parcial_usuario(gc, pontuacao_usuario, jogos, usuarios, SHEET_ID):

    if pontuacao_usuario.empty:
        df_base = usuarios[['email']].copy()

        grupos = jogos['grupo'].dropna().unique()

        for g in grupos:
            df_base[f'grupo_{g}'] = 0

        df_base['total'] = 0

        preencher_planilha_df(gc, 'parcial_usuario', df_base, SHEET_ID)
        return None

    mapa_grupos = dict(zip(jogos['id'], jogos['grupo']))
    pontuacao_usuario['grupo'] = pontuacao_usuario['jogo_id'].map(mapa_grupos)

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
    df_final = usuarios[['email']].merge(df_final, on='email', how='left').fillna(0)

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