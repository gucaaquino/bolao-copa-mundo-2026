import pandas as pd
import json
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import pytz
import random
import os

SHEET_ID    = os.environ['SHEET_ID']
CREDENTIALS = json.loads(os.environ['GOOGLE_CREDENTIALS'])
BR_TZ       = pytz.timezone('America/Sao_Paulo')
SCOPES      = ['https://spreadsheets.google.com/feeds',
               'https://www.googleapis.com/auth/drive']

def autenticar_sheets():
    creds = Credentials.from_service_account_info(CREDENTIALS, scopes=SCOPES)
    return gspread.authorize(creds)

def formatar_data_hora(utc_str):
    if not utc_str:
        return '-', '-'
    dt = datetime.fromisoformat(utc_str.replace('Z', '+00:00'))
    dt_br = dt.astimezone(BR_TZ)
    return dt_br.strftime('%d/%m/%Y'), dt_br.strftime('%H:%M')

def traduzir_status(status):
    mapa = {
        'SCHEDULED':        'agendado',
        'TIMED':            'agendado',
        'IN_PLAY':          'em_andamento',
        'PAUSED':           'em_andamento',
        'FINISHED':         'encerrado',
        'EXTRA_TIME':       'em_andamento',
        'PENALTY_SHOOTOUT': 'em_andamento',
        'SUSPENDED':        'cancelado',
        'POSTPONED':        'adiado',
        'CANCELLED':        'cancelado',
        'AWARDED':          'encerrado'
    }

    return mapa.get(status, status)

def montar_planilha_jogos(gc, jogos):
    nome_aba  = 'jogos'
    cabecalho = ['data', 'hora', 'sigla_casa', 'sigla_fora', 'grupo']
    dados     = [cabecalho]

    for p in jogos:
        data, hora    = formatar_data_hora(p.get('utcDate'))
        sigla_casa    = p['homeTeam'].get('tla')
        sigla_fora    = p['awayTeam'].get('tla')

        grupo = random.choice(['A', 'B'])
        data = '25/03/2026'

        dados.append([data, hora, sigla_casa, sigla_fora, grupo])

    preencher_planilha(gc, nome_aba, dados)

def montar_planilha_resultados(gc, jogos):
    nome_aba  = 'resultados'
    cabecalho = ['data', 'hora', 'status', 'sigla_casa', 'sigla_fora', 'gols_casa', 'gols_fora', 'grupo']
    dados     = [cabecalho]

    for p in jogos:
        data, hora   = formatar_data_hora(p.get('utcDate'))
        status       = traduzir_status(p.get('status'))
        sigla_casa   = p['homeTeam'].get('tla')
        sigla_fora   = p['awayTeam'].get('tla')
        gols_casa    = p['score']['fullTime']['home']
        gols_fora    = p['score']['fullTime']['away']

        grupo = random.choice(['A', 'B'])
        data = '25/03/2026'

        dados.append([data, hora, status, sigla_casa, sigla_fora, str(gols_casa) if gols_casa is not None else '', str(gols_fora) if gols_fora is not None else '', grupo])
      
    preencher_planilha(gc, nome_aba, dados)

def montar_planilha_times(gc, times):
    nome_aba  = 'times'
    cabecalho = ['nome', 'sigla']
    dados = [cabecalho]

    for t in times:
        dados.append(t)

    preencher_planilha(gc, nome_aba, dados)

def preencher_planilha(gc, nome_aba, dados):
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

def ler_planiha(gc, nome_aba):
    sh = gc.open_by_key(SHEET_ID)
    abas = [a.title for a in sh.worksheets() if a.title == nome_aba]

    if len(abas) < 1:
        print(f'❌ Nenhuma aba {nome_aba} encontrada.')
        return None
        
    print(f'📋 Lendo aba: {nome_aba}')

    aba = sh.worksheet(nome_aba)
    dados = aba.get_all_records()

    return pd.DataFrame(dados)