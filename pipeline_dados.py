"""Pipeline de dados do Quem e o Craque.

Roda em sequencia os scrapers que geram os arquivos usados pelo jogo:
  dados.js / dados.txt   (pegar_dados.py)      jogadores, clubes, valores e fama
  gols.js / gols.json    (pegar_gols.py)       gols e jogos por jogador
  historico.js / .json   (pegar_historico.py)  titulos oficiais + trajetoria de clubes
  copas.js / copas.json  (pegar_copas.py)      copas (raro: so quando a fonte muda)
  reputacao_clubes.json  (gerar_reputacao.py)  reputacao/divisao real dos clubes (titulos fieis)

Escopos (--escopo):
  clubes     baixa todas as ligas, atualiza dados.txt/dados.js e recalcula a fama
  fama       so recalcula a fama (0 requisicoes) usando gols.json + copas_tm.json
  gols       atualiza gols/jogos (retoma de onde parou) e recalcula a fama
  historico  atualiza titulos/trajetoria (retoma de onde parou)
  reputacao  so refaz o reputacao_clubes.json (casamento com a base do Copero)
  tudo       clubes + gols + historico + fama

Obs.: clubes/fama/gols/tudo regravam o dados.js, entao ao final o pipeline refaz
o reputacao_clubes.json sozinho (os nomes dos clubes podem ter mudado).

Opcoes:
  --limite N   limita quantos jogadores os passos de gols/historico processam
  --sem-bonus  recalcula a fama sem os bonus de gols/copas
  --seco       so mostra os comandos, sem executar

Exemplos:
  python pipeline_dados.py --escopo tudo --limite 2000
  python pipeline_dados.py --escopo fama
  python pipeline_dados.py --escopo clubes --sem-bonus
"""
import argparse
import json
import os
import subprocess
import sys
import time

AQUI = os.path.dirname(os.path.abspath(__file__))
BONUS = ("--gols", "gols.json", "--copas-tm", "copas_tm.json")


ARQUIVOS_LF = ("dados.js", "gols.js", "gols.json", "copas.js", "copas.json",
               "copero-times.js", "historico.js", "historico.json",
               "reputacao_clubes.json")


def normalizar_lf():
    """Converte CRLF -> LF nos arquivos publicados.

    Sem isso, o mesmo arquivo gerado no Windows (CRLF) e no Linux (LF) aparece
    como "todas as linhas mudaram" no git, inchando o repositorio a cada rodada.
    """
    for arq in ARQUIVOS_LF:
        p = os.path.join(AQUI, arq)
        if not os.path.exists(p):
            continue
        with open(p, "rb") as f:
            b = f.read()
        if b"\r\n" in b:
            with open(p, "wb") as f:
                f.write(b.replace(b"\r\n", b"\n"))
            print("  (normalizado para LF: %s)" % arq, flush=True)


def passo(nome, cmd, seco=False):
    print("\n=== %s ===" % nome, flush=True)
    print("> " + " ".join(cmd), flush=True)
    if seco:
        return 0.0
    t = time.time()
    env = dict(os.environ)
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONUNBUFFERED"] = "1"
    r = subprocess.run(cmd, cwd=AQUI, env=env)
    dt = time.time() - t
    if r.returncode != 0:
        print("!!! passo '%s' falhou (codigo %d)" % (nome, r.returncode))
        sys.exit(r.returncode)
    normalizar_lf()
    print("--- %s: ok em %.1f min" % (nome, dt / 60.0), flush=True)
    return dt


def passo_fama(seco, com_bonus):
    cmd = [sys.executable, "pegar_dados.py", "--so-fama", "--html", "dados.js"]
    if com_bonus:
        cmd += list(BONUS)
    return passo("fama", cmd, seco)


def passo_clubes(seco, com_bonus):
    # --sem-cache: o cache das paginas de elenco envelhece (transferencias!)
    cmd = [sys.executable, "pegar_dados.py", "--sem-cache", "--html", "dados.js"]
    if com_bonus:
        cmd += list(BONUS)
    return passo("clubes", cmd, seco)


def passo_gols(seco, limite):
    cmd = [sys.executable, "pegar_gols.py", "--dados", "dados.txt"]
    if limite:
        cmd += ["--limite", str(limite)]
    return passo("gols", cmd, seco)


def passo_historico(seco, limite):
    cmd = [sys.executable, "pegar_historico.py", "--dados", "dados.txt"]
    if limite:
        cmd += ["--limite", str(limite)]
    return passo("historico", cmd, seco)


def passo_reputacao(seco):
    return passo("reputacao", [sys.executable, "gerar_reputacao.py"], seco)


def garantir_dados_txt(seco, com_bonus):
    """gols/historico leem dados.txt; se ele nao existir, a fama o recria do dados.js."""
    if os.path.exists(os.path.join(AQUI, "dados.txt")):
        return
    print("\n(dados.txt ausente: recriando a partir do dados.js)")
    passo_fama(seco, com_bonus)


def resumo():
    print("\n=== arquivos ===")
    for arq in ("dados.js", "dados.txt", "gols.js", "gols.json", "historico.js",
                "historico.json", "reputacao_clubes.json"):
        p = os.path.join(AQUI, arq)
        if not os.path.exists(p):
            print("  %-16s ausente" % arq)
            continue
        kb = os.path.getsize(p) / 1024.0
        extra = ""
        if arq.endswith(".json"):
            try:
                d = json.load(open(p, encoding="utf-8"))
                rows = d.get("rows", d)
                extra = " | %d registros" % len(rows)
            except Exception:
                pass
        print("  %-16s %8.0f KB%s" % (arq, kb, extra))


def main():
    ap = argparse.ArgumentParser(description="Pipeline de dados do Quem e o Craque")
    ap.add_argument("--escopo", default="clubes",
                    choices=["clubes", "fama", "gols", "historico", "reputacao", "tudo"])
    ap.add_argument("--limite", type=int, help="limite de jogadores nos passos de gols/historico")
    ap.add_argument("--sem-bonus", action="store_true",
                    help="nao usa os bonus de gols.json/copas_tm.json na fama")
    ap.add_argument("--seco", action="store_true", help="so mostra os comandos")
    a = ap.parse_args()

    com_bonus = not a.sem_bonus
    if com_bonus:
        faltando = [f for f in ("gols.json", "copas_tm.json") if not os.path.exists(os.path.join(AQUI, f))]
        if faltando:
            print("aviso: sem os bonus de fama (%s nao encontrado)" % ", ".join(faltando))
            com_bonus = False

    t0 = time.time()
    print("Escopo: %s%s%s" % (a.escopo, " | limite %d" % a.limite if a.limite else "",
                              "" if com_bonus else " | sem bonus de fama"))
    e = a.escopo
    if e in ("clubes", "tudo"):
        passo_clubes(a.seco, com_bonus)
    if e in ("gols", "tudo"):
        garantir_dados_txt(a.seco, com_bonus)
        passo_gols(a.seco, a.limite)
    if e in ("historico", "tudo"):
        garantir_dados_txt(a.seco, com_bonus)
        passo_historico(a.seco, a.limite)
    if e in ("fama", "gols", "tudo"):
        # fama por ultimo: usa o gols.json recem-gerado no bonus de gols
        passo_fama(a.seco, com_bonus)
    if e in ("clubes", "fama", "gols", "tudo", "reputacao"):
        # dados.js pode ter sido regravado: refaz as reputacoes reais dos clubes
        passo_reputacao(a.seco)

    resumo()
    print("\nTotal: %.1f min" % ((time.time() - t0) / 60.0))


if __name__ == "__main__":
    main()
