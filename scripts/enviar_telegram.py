import os
import json
import requests
import gspread
from google.oauth2.service_account import Credentials

# ── Configuração ──────────────────────────────────────────
TELEGRAM_TOKEN   = os.environ['TELEGRAM_TOKEN']
TELEGRAM_CHAT_ID = os.environ['TELEGRAM_CHAT_ID']
SHEET_ID         = os.environ['SHEET_ID']
CREDENTIALS      = json.loads(os.environ['GOOGLE_CREDENTIALS'])
SCOPES           = ['https://spreadsheets.google.com/feeds',
                    'https://www.googleapis.com/auth/drive']

# ── Autenticação Google Sheets ────────────────────────────
def autenticar_sheets():
    creds = Credentials.from_service_account_info(CREDENTIALS, scopes=SCOPES)
    return gspread.authorize(creds)

# ── Lê última rodada da planilha ──────────────────────────
def get_ultima_rodada(gc):
    sh   = gc.open_by_key(SHEET_ID)
    abas = [a.title for a in sh.worksheets() if a.title.startswith('Rodada')]

    if not abas:
        raise Exception('Nenhuma aba de rodada encontrada na planilha.')

    abas_ordenadas = sorted(abas, key=lambda x: int(x.replace('Rodada ', '')))
    ultima         = abas_ordenadas[-1]
    print(f'📋 Lendo aba: {ultima}')

    aba    = sh.worksheet(ultima)
    dados  = aba.get_all_records()
    numero = int(ultima.replace('Rodada ', ''))
    return numero, dados

# ── Formata mensagem ──────────────────────────────────────
def formatar_mensagem(rodada, jogos):
    linhas = [f'<b>⚽ Brasileirão — Rodada {rodada}</b>\n']

    for j in jogos:
        time_casa = j.get('Time Casa', '-')
        time_fora = j.get('Time Fora', '-')
        gols_casa = j.get('Gols Casa', '-')
        gols_fora = j.get('Gols Fora', '-')
        status    = j.get('Status', '-')
        data      = j.get('Data', '')
        hora      = j.get('Hora', '')

        if '✅' in str(status):
            linha = f'✅ {time_casa} <b>{gols_casa} x {gols_fora}</b> {time_fora}'
        elif '🔴' in str(status):
            linha = f'🔴 {time_casa} <b>{gols_casa} x {gols_fora}</b> {time_fora} <i>(ao vivo)</i>'
        else:
            linha = f'📅 {time_casa} x {time_fora} — {data} {hora}'

        linhas.append(linha)

    return '\n'.join(linhas)

# ── Envia para o Telegram ─────────────────────────────────
def enviar_telegram(mensagem):
    url     = f'https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage'
    payload = {
        'chat_id':    TELEGRAM_CHAT_ID,
        'text':       mensagem,
        'parse_mode': 'HTML'
    }
    r = requests.post(url, data=payload)
    if r.status_code == 200:
        print('✅ Mensagem enviada no Telegram!')
    else:
        raise Exception(f'Erro ao enviar para o Telegram: {r.text}')

# ── Main ──────────────────────────────────────────────────
if __name__ == '__main__':
    gc             = autenticar_sheets()
    rodada, jogos  = get_ultima_rodada(gc)
    mensagem       = formatar_mensagem(rodada, jogos)
    print('\n--- Preview ---')
    print(mensagem)
    print('---------------\n')
    enviar_telegram(mensagem)