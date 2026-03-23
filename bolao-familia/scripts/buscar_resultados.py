import os
import json
import requests
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import pytz

# ── Configuração ──────────────────────────────────────────
API_TOKEN   = os.environ['FOOTBALL_API_TOKEN']
SHEET_ID    = os.environ['SHEET_ID']
CREDENTIALS = json.loads(os.environ['GOOGLE_CREDENTIALS'])
COMPETITION = 'BSA'
BASE_URL    = 'https://api.football-data.org/v4'
BR_TZ       = pytz.timezone('America/Sao_Paulo')
SCOPES      = ['https://spreadsheets.google.com/feeds',
               'https://www.googleapis.com/auth/drive']

# ── Autenticação Google Sheets ────────────────────────────
def autenticar_sheets():
    creds = Credentials.from_service_account_info(CREDENTIALS, scopes=SCOPES)
    return gspread.authorize(creds)

# ── Funções auxiliares ────────────────────────────────────
def formatar_data_hora(utc_str):
    if not utc_str:
        return '-', '-'
    dt = datetime.fromisoformat(utc_str.replace('Z', '+00:00'))
    dt_br = dt.astimezone(BR_TZ)
    return dt_br.strftime('%d/%m/%Y'), dt_br.strftime('%H:%M')

def traduzir_status(status):
    mapa = {
        'SCHEDULED':        '📅 Agendado',
        'TIMED':            '📅 Agendado',
        'IN_PLAY':          '🔴 Ao Vivo',
        'PAUSED':           '⏸ Intervalo',
        'FINISHED':         '✅ Encerrado',
        'EXTRA_TIME':       '⏱ Prorrogação',
        'PENALTY_SHOOTOUT': '🥅 Pênaltis',
        'SUSPENDED':        '⚠️ Suspenso',
        'POSTPONED':        '📆 Adiado',
        'CANCELLED':        '❌ Cancelado',
        'AWARDED':          '🏆 WO'
    }
    return mapa.get(status, status)

# ── Busca rodada atual ────────────────────────────────────
def buscar_rodada_atual():
    headers = {'X-Auth-Token': API_TOKEN}

    r = requests.get(f'{BASE_URL}/competitions/{COMPETITION}', headers=headers)
    r.raise_for_status()
    rodada_atual = r.json()['currentSeason']['currentMatchday']
    print(f'📅 Rodada atual: {rodada_atual}')

    r = requests.get(
        f'{BASE_URL}/competitions/{COMPETITION}/matches',
        headers=headers,
        params={'matchday': rodada_atual}
    )
    r.raise_for_status()
    partidas = r.json()['matches']
    print(f'⚽ {len(partidas)} jogos encontrados')
    return rodada_atual, partidas

# ── Preenche planilha ─────────────────────────────────────
def preencher_planilha(gc, rodada, partidas):
    sh       = gc.open_by_key(SHEET_ID)
    nome_aba = f'Rodada {rodada}'

    try:
        aba = sh.worksheet(nome_aba)
        aba.clear()
        print(f'🔄 Aba "{nome_aba}" limpa')
    except gspread.exceptions.WorksheetNotFound:
        aba = sh.add_worksheet(title=nome_aba, rows=20, cols=8)
        print(f'✨ Aba "{nome_aba}" criada')

    cabecalho = ['Data', 'Hora', 'Status', 'Time Casa', 'Gols Casa', 'x', 'Gols Fora', 'Time Fora']
    linhas    = [cabecalho]

    for p in partidas:
        data, hora   = formatar_data_hora(p.get('utcDate'))
        status       = traduzir_status(p.get('status'))
        time_casa    = p['homeTeam'].get('shortName') or p['homeTeam']['name']
        time_fora    = p['awayTeam'].get('shortName') or p['awayTeam']['name']
        gols_casa    = p['score']['fullTime']['home']
        gols_fora    = p['score']['fullTime']['away']

        linhas.append([
            data, hora, status, time_casa,
            str(gols_casa) if gols_casa is not None else '-',
            'x',
            str(gols_fora) if gols_fora is not None else '-',
            time_fora
        ])

    aba.update('A1', linhas)
    print(f'✅ Planilha atualizada com {len(partidas)} jogos!')

# ── Main ──────────────────────────────────────────────────
if __name__ == '__main__':
    gc              = autenticar_sheets()
    rodada, partidas = buscar_rodada_atual()
    preencher_planilha(gc, rodada, partidas)