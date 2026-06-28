import os
from scripts.utils import api_google as ag
from scripts.utils import api_whatsapp as aw
import pandas as pd

SHEET_ID                 = os.environ['SHEET_ID']
gc                       = ag.autenticar_sheets()

palpites_mata_mata = ag.ler_planiha_df(gc, 'palpites_mata_mata', SHEET_ID)

def to_int(val):
    """Converte para int com segurança — retorna None se vazio, NaN ou inválido."""
    try:
        if pd.isna(val):
            return None
    except (TypeError, ValueError):
        pass

    try:
        return int(str(val).strip())
    except (ValueError, TypeError):
        return None

def relatorio_mata_mata_whatsapp(palpites_mata_mata_df):
    """
    Gera mensagem WhatsApp com palpites do mata-mata agrupados por jogo.

    Parâmetros
    ----------
    palpites_mata_mata_df : DataFrame com colunas:
        nome, email, telefone, jogo_id, time_casa, gol_casa, time_fora, gol_fora
    """

    df = palpites_mata_mata_df.copy()

    # ── Alias: primeiro e último nome ─────────────────────────────────────────
    def alias(nome):
        partes = str(nome).strip().split()
        if len(partes) == 1:
            return partes[0]
        return f"{partes[0]} {partes[-1]}"

    df["alias"] = df["nome"].apply(alias)

    # ── Ordena por jogo_id e depois por nome ──────────────────────────────────
    df = df.sort_values(["jogo_id", "nome"]).reset_index(drop=True)

    linhas = []
    linhas.append("🏆 *Palpites — Fase Mata-Mata*")

    jogo_atual = None

    for _, row in df.iterrows():
        jogo_id   = str(row["jogo_id"]).strip()
        time_casa = str(row["time_casa"]).strip()
        time_fora = str(row["time_fora"]).strip()

        # ── Cabeçalho do jogo ─────────────────────────────────────────────────
        if jogo_id != jogo_atual:
            jogo_atual = jogo_id
            linhas.append("")
            linhas.append(f"⚽ *{time_casa} x {time_fora}*")
            linhas.append("")

        # ── Palpite da pessoa ─────────────────────────────────────────────────
        gc = to_int(row["gol_casa"])
        gf = to_int(row["gol_fora"])

        if gc is not None and gf is not None:
            palpite_str = f"{gc} x {gf}"
        else:
            palpite_str = "não enviado"

        linhas.append(f"  👤 {row['alias']}: {time_casa} *{palpite_str}* {time_fora}")

    linhas.append("")
    linhas.append("━━━━━━━━━━━━━━")

    n_jogos   = df["jogo_id"].nunique()
    n_pessoas = df["alias"].nunique()
    linhas.append(f"📊 {n_jogos} jogo{'s' if n_jogos != 1 else ''} | {n_pessoas} participante{'s' if n_pessoas != 1 else ''}")

    return "\n".join(linhas)

msg = relatorio_mata_mata_whatsapp(palpites_mata_mata)
print(msg)

aw.enviar_whatsapp(msg, '5519997725964')
