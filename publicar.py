"""Publica os dados atualizados no repositorio do GitHub (fallback local).

Use depois de rodar o pipeline_dados.py no PC: copia os arquivos gerados para o
clone do repositorio e faz commit + push. O commit sai com [skip netlify] para
nao gastar deploy na Netlify (o Cloudflare Pages constroi normalmente).

Uso (na pasta do jogo):
  python publicar.py                    # dados + scripts
  python publicar.py --jogo             # inclui o index6.html -> index.html
  python publicar.py --seco             # so mostra o que mudaria
  python publicar.py -m "mensagem"      # mensagem do commit
  python publicar.py --alvo C:\\dev\\quem-e-o-craque
"""
import argparse
import os
import shutil
import subprocess
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
ALVO_PADRAO = r"C:\dev\quem-e-o-craque"

DADOS = ["dados.js", "gols.js", "gols.json", "copas.js", "copas.json",
         "copero-times.js", "historico.js", "historico.json", "famosos.txt", "copas_tm.json"]
SCRIPTS = ["pipeline_dados.py", "publicar.py", "pegar_dados.py", "pegar_gols.py",
           "pegar_historico.py", "pegar_copas.py", "pegar_copas2.py",
           "cruzar_copas.py", "fama_copas.py"]


def git(*args, alvo="."):
    exe = shutil.which("git") or r"C:\Program Files\Git\cmd\git.exe"
    return subprocess.run([exe, "-C", alvo] + list(args), text=True,
                          capture_output=True, encoding="utf-8", errors="replace")


def main():
    ap = argparse.ArgumentParser(description="Publica os dados no repositorio do GitHub")
    ap.add_argument("--alvo", default=ALVO_PADRAO, help="pasta do clone do repositorio")
    ap.add_argument("--jogo", action="store_true", help="inclui o index6.html como index.html")
    ap.add_argument("-m", "--mensagem", default="dados atualizados", help="mensagem do commit")
    ap.add_argument("--seco", action="store_true", help="so mostra o que mudaria")
    a = ap.parse_args()

    alvo = os.path.abspath(a.alvo)
    if not os.path.isdir(os.path.join(alvo, ".git")):
        print("ERRO: %s nao parece um clone do repositorio (.git nao encontrado)." % alvo)
        print("Clone uma vez com:  git clone https://github.com/daniellg2/quem-e-o-craque.git \"%s\"" % alvo)
        sys.exit(1)

    arquivos = list(DADOS) + list(SCRIPTS)
    if a.jogo:
        arquivos.append("index6.html")

    copiados, faltando = [], []
    for f in arquivos:
        src = os.path.join(AQUI, f)
        if not os.path.exists(src):
            faltando.append(f)
            continue
        dst_nome = "index.html" if f == "index6.html" else f
        dst = os.path.join(alvo, dst_nome)
        novo = (not os.path.exists(dst)) or (os.path.getsize(dst) != os.path.getsize(src)) or \
               (open(dst, "rb").read() != open(src, "rb").read())
        if novo:
            if not a.seco:
                shutil.copy2(src, dst)
            copiados.append(dst_nome)

    if faltando:
        print("aviso: nao encontrei na pasta do jogo: %s" % ", ".join(faltando))
    if not copiados:
        print("Nada para publicar: os arquivos do repositorio ja estao iguais.")
        return

    print("Copiados para o repositorio: %s" % ", ".join(copiados))
    if a.seco:
        print("(--seco: nada foi copiado nem enviado)")
        return

    msg = a.mensagem
    if "[skip netlify]" not in msg and "[skip ci]" not in msg:
        msg += " [skip netlify]"

    git("add", "-A", alvo=alvo)
    st = git("status", "--porcelain", alvo=alvo)
    print("\n--- git status ---\n%s" % (st.stdout.strip() or "(vazio)"))
    r = git("commit", "-m", msg, alvo=alvo)
    print("\n--- git commit ---\n%s" % (r.stdout.strip() or r.stderr.strip()))
    if r.returncode != 0:
        print("nada para commitar?")
        return
    p = git("push", "origin", "main", alvo=alvo)
    print("\n--- git push ---\n%s%s" % (p.stdout.strip(), p.stderr.strip()))
    print("\nPublicado (a Cloudflare Pages deve construir em ~1 minuto).")


if __name__ == "__main__":
    main()
