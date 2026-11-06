"""Publica os dados atualizados no repositorio do GitHub (fallback local).

Use depois de rodar o pipeline_dados.py no PC: copia os arquivos gerados para o
clone do repositorio e faz commit + push. O commit sai com [skip netlify] para
nao gastar deploy na Netlify (o Cloudflare Pages constroi normalmente).

Uso (na pasta do jogo):
  python publicar.py                    # dados + scripts
  python publicar.py --jogo             # inclui index.html, JS do jogo e todos os assets
  python publicar.py --seco             # so mostra o que mudaria
  python publicar.py -m "mensagem"      # mensagem do commit
  python publicar.py --alvo C:\\dev\\quem-e-o-craque
"""
import argparse
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

AQUI = os.path.dirname(os.path.abspath(__file__))
ALVO_PADRAO = r"C:\dev\quem-e-o-craque"

DADOS = ["dados.js", "gols.js", "gols.json", "copas.js", "copas.json",
         "copero-times.js", "historico.js", "historico.json", "famosos.txt", "copas_tm.json",
         "reputacao_clubes.json", "reputacao_clubes.js", "netlify.toml"]
SCRIPTS = ["pipeline_dados.py", "publicar.py", "pegar_dados.py", "pegar_gols.py",
           "pegar_historico.py", "pegar_gemeos.py", "gemeos_transfermarkt.py", "revisar_gemeos.py", "pegar_copas.py", "pegar_copas2.py",
           "cruzar_copas.py", "fama_copas.py", "gerar_reputacao.py", "testar_sportdb.py", "testar_gemeo_gemini.py"]
EXTRAS = ["README.md", "publicar.cmd", "atualizar_dados.cmd", "atualizar_dados.ps1", ".gitignore",
          "wrangler.jsonc", ".assetsignore", "_headers", "worker.js"]
PASTA_ASSETS = "assets"
ARQUIVOS_JOGO = ["index.html", "privacidade.html", "termos.html", "legal.css", "career-divisions.js", "motor-copero.js", "copero-serie-d.js", "copero-angola-tahiti.js"]

ARQUIVOS_LF = ("dados.js", "gols.js", "gols.json", "copas.js", "copas.json",
               "copero-times.js", "historico.js", "historico.json",
               "reputacao_clubes.json")


def normalizar_lf():
    """CRLF -> LF nos arquivos publicados.

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
            print("  (normalizado para LF: %s)" % arq)


def assets_do_jogo():
    """Lista todos os assets locais, preservando a estrutura de pastas."""
    pasta = os.path.join(AQUI, PASTA_ASSETS)
    if not os.path.isdir(pasta):
        raise FileNotFoundError("pasta de assets nao encontrada: %s" % pasta)
    arquivos = []
    for base, _, nomes in os.walk(pasta):
        for nome in nomes:
            arquivos.append(os.path.relpath(os.path.join(base, nome), AQUI))
    arquivos.sort()
    with open(os.path.join(AQUI, "index.html"), encoding="utf-8") as f:
        referencias = set(re.findall(r"assets/[\w./-]+\.(?:webp|png|jpg|jpeg|svg|gif)", f.read(), re.I))
    faltando = [r for r in referencias if not os.path.isfile(os.path.join(AQUI, *r.split("/")))]
    if faltando:
        raise FileNotFoundError("assets citados no index.html nao encontrados: %s" % ", ".join(sorted(faltando)))
    return arquivos


def git(*args, alvo=".", entrada=None):
    exe = shutil.which("git") or r"C:\Program Files\Git\cmd\git.exe"
    return subprocess.run([exe, "-C", alvo, "--literal-pathspecs"] + list(args), text=True,
                          input=entrada, capture_output=True, encoding="utf-8", errors="replace")


def git_ok(*args, alvo, entrada=None):
    resultado = git(*args, alvo=alvo, entrada=entrada)
    if resultado.returncode != 0:
        raise RuntimeError("git %s falhou:\n%s" % (args[0], resultado.stderr.strip() or resultado.stdout.strip()))
    return resultado.stdout.strip()


def assets_dos_dados():
    """As imagens referenciadas pela base precisam acompanhar ate publicacoes sem --jogo."""
    texto = Path(AQUI, "dados.js").read_text(encoding="utf-8")
    refs = sorted(set(re.findall(r"assets/database/[\w/-]+\.(?:png|jpg|webp|gif|svg)", texto)))
    faltando = [r for r in refs if not Path(AQUI, r).is_file()]
    if faltando:
        raise FileNotFoundError("imagens da base ausentes: " + ", ".join(faltando))
    if refs:
        if not Path(AQUI, "imagens-offline.js").is_file():
            raise FileNotFoundError("imagens-offline.js ausente; gere a versao offline antes de publicar.")
        refs.append("imagens-offline.js")
    return refs


def commits_da_publicacao(alvo, permitidos):
    """Valida o historico de um SHA fixo, inclusive se outro processo mover a branch."""
    head = git_ok("rev-parse", "HEAD", alvo=alvo)
    pendentes = git_ok("rev-list", "origin/main.." + head, alvo=alvo).splitlines()
    for commit in pendentes:
        mensagem = git_ok("show", "-s", "--format=%s", commit, alvo=alvo)
        caminhos = [p for p in git_ok("diff-tree", "--no-commit-id", "--name-only", "-z", "-r", "--root", commit, alvo=alvo).split("\0") if p]
        pais = git_ok("show", "-s", "--format=%P", commit, alvo=alvo).split()
        if len(pais) > 1 or "[skip netlify]" not in mensagem or not caminhos or not set(caminhos) <= permitidos:
            raise RuntimeError("Ha commit pendente fora desta publicacao: %s. Revise-o antes de enviar." % commit)
    return head, pendentes


def main():
    ap = argparse.ArgumentParser(description="Publica os dados no repositorio do GitHub")
    ap.add_argument("--alvo", default=ALVO_PADRAO, help="pasta do clone do repositorio")
    ap.add_argument("--jogo", action="store_true", help="inclui index.html, JS do jogo e todos os assets")
    ap.add_argument("-m", "--mensagem", default="dados atualizados", help="mensagem do commit")
    ap.add_argument("--incluir", default="",
                    help="arquivos extras para publicar (separados por virgula). Ex.: --incluir times.js")
    ap.add_argument("--seco", action="store_true", help="so mostra o que mudaria")
    a = ap.parse_args()

    alvo = os.path.abspath(a.alvo)
    raiz = git_ok("rev-parse", "--show-toplevel", alvo=alvo)
    if Path(raiz).resolve() != Path(alvo).resolve():
        raise RuntimeError("--alvo precisa apontar para a raiz do clone.")
    if git_ok("branch", "--show-current", alvo=alvo) != "main":
        raise RuntimeError("O clone precisa estar na branch main; nenhuma troca foi feita.")
    estado = git_ok("status", "--porcelain", "--untracked-files=all", alvo=alvo)
    if estado:
        raise RuntimeError("O clone tem alteracoes locais. Revise ou guarde-as antes de publicar; nada foi copiado.\n" + estado)

    arquivos = list(DADOS) + list(SCRIPTS) + list(EXTRAS) + assets_dos_dados()
    if a.jogo:
        arquivos.extend(ARQUIVOS_JOGO)
        try:
            arquivos.extend(assets_do_jogo())
        except FileNotFoundError as e:
            print("ERRO: %s" % e)
            sys.exit(1)
    arquivos += [s.strip() for s in a.incluir.split(",") if s.strip()]
    arquivos = list(dict.fromkeys(f.replace("\\", "/") for f in arquivos))
    for f in arquivos:
        if (Path(f).is_absolute() or not Path(AQUI, f).resolve().is_relative_to(Path(AQUI).resolve())
                or not Path(alvo, f).resolve().is_relative_to(Path(alvo).resolve())):
            raise ValueError("Caminho fora da pasta de origem ou destino: " + f)
        if Path(AQUI, f).exists() and not Path(AQUI, f).is_file():
            raise ValueError("A publicacao aceita apenas arquivos: " + f)
        if Path(alvo, f).is_symlink():
            raise ValueError("O destino nao pode ser um link simbolico: " + f)

    # Um push que falhou pode ser retomado, mas commits alheios nao sao enviados junto.
    permitidos = set(arquivos)
    head_inicial, pendentes = commits_da_publicacao(alvo, permitidos)

    if not a.seco:
        normalizar_lf()

    copiados, faltando = [], []
    for f in arquivos:
        src = os.path.join(AQUI, f)
        if not os.path.exists(src):
            faltando.append(f)
            continue
        dst_nome = f
        dst = os.path.join(alvo, dst_nome)
        novo = not os.path.exists(dst) or Path(dst).read_bytes() != Path(src).read_bytes()
        if novo:
            if not a.seco:
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                shutil.copyfile(src, dst)
            copiados.append(dst_nome)

    if faltando:
        print("aviso: nao encontrei na pasta do jogo: %s" % ", ".join(faltando))
    if not copiados and not pendentes:
        print("Nada para publicar: os arquivos do repositorio ja estao iguais.")
        return

    if a.seco:
        print("Alteracoes previstas: %s" % ", ".join(copiados))
        print("Commits pendentes para enviar: %d" % len(pendentes))
        print("(--seco: nada foi copiado nem enviado)")
        return

    print("Copiados para o repositorio: %s" % ", ".join(copiados))

    msg = a.mensagem
    if "[skip netlify]" not in msg:
        msg += " [skip netlify]"

    if copiados:
        if (git_ok("rev-parse", "HEAD", alvo=alvo) != head_inicial
                or git_ok("branch", "--show-current", alvo=alvo) != "main"):
            raise RuntimeError("A branch mudou durante a copia. Os arquivos foram preservados; revise o clone.")
        caminhos = "\0".join(copiados) + "\0"
        git_ok("add", "--pathspec-from-file=-", "--pathspec-file-nul", alvo=alvo, entrada=caminhos)
        print(git_ok("commit", "--only", "-m", msg, "--pathspec-from-file=-", "--pathspec-file-nul", alvo=alvo, entrada=caminhos))
    head, _ = commits_da_publicacao(alvo, permitidos)
    print(git_ok("push", "origin", head + ":refs/heads/main", alvo=alvo))
    print("\nEnviado ao GitHub. Confira o resultado do deploy na Cloudflare.")


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, RuntimeError) as exc:
        print("ERRO: %s" % exc, file=sys.stderr)
        sys.exit(1)
