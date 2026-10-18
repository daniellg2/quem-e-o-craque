"""
Cruza os jogadores do copas.js (oGol) com o dados.txt (Transfermarkt) e gera copas_tm.json.

NAO altera nenhum nome dos arquivos. O cruzamento é feito por chave, em ordem de confiança:

  1. manual     : ids_copa.txt  ("ID_oGol  ID_TM  # nome")  -> vence tudo
  2. exato      : nome normalizado (sem acento, minúsculo) + país, único
  3. parcial    : todas as palavras do nome mais curto aparecem no outro (ex.: "Alisson" ⊂ "Alisson Becker")
  4. sobrenome  : primeira e última palavra iguais (ex.: "Dani Alves" x "Daniel Alves" NÃO cai aqui: use manual)
  Em 2, 3 e 4 o candidato também precisa ter idade compatível: ano da Copa - idade na Copa
  deve ficar a até 2 anos do ano de nascimento estimado pelo dados.txt (2026 - idade atual).
  Empate ou nenhum candidato = não casado (fica na lista para revisão).

Uso (na pasta do projeto, com copas.js, dados.txt e, se existir, ids_copa.txt):
  python cruzar_copas.py
  python cruzar_copas.py --copas copas.js --dados dados.txt --saida copas_tm.json
"""
import argparse, csv, json, re, sys
from collections import defaultdict

import pegar_dados as pd   # reaproveita _norm, _pais e ler_linhas_dados (mesma pasta)

ANO_REF = 2026
TOLERANCIA_IDADE = 2


def carregar_copas(caminho):
    with open(caminho, encoding="utf-8") as f:
        txt = f.read()
    if txt.startswith("window.COPAS_DATA="):
        txt = txt[len("window.COPAS_DATA="):].rstrip().rstrip(";")
    return json.loads(txt)["rows"]


def carregar_manual(caminho):
    """ids_copa.txt: 'ID_oGol ID_TM  # comentario'. Linhas com # no início são ignoradas."""
    manual = {}
    try:
        with open(caminho, encoding="utf-8") as f:
            for linha in f:
                m = re.match(r"\s*(\d+)\s+(\d+)", linha)
                if m:
                    manual[m.group(1)] = m.group(2)
    except OSError:
        pass
    return manual


# letras que a normalização padrão (NFD + ASCII) apagaria: Groß viraria "gro"
LETRAS = {"ß": "ss", "ø": "o", "æ": "ae", "œ": "oe", "ł": "l", "đ": "d", "ð": "d", "þ": "th", "ı": "i"}


def nome_norm(t):
    t = (t or "").lower()
    for a, b in LETRAS.items():
        t = t.replace(a, b)
    return pd._norm(t)


# países com nome diferente no copas.js e no dados.txt (chave e valor já normalizados por pd._pais)
ALIAS_PAIS = {
    pd._pais("Catar"): pd._pais("Qatar"),
    pd._pais("Rep. Dem. do Congo"): pd._pais("RD do Congo"),
    pd._pais("Tchéquia"): pd._pais("República Checa"),
    pd._pais("Coreia do Sul"): pd._pais("Coreia do Sul"),
}


def pais_do_copa(nome_pais):
    p = pd._pais(nome_pais)
    return ALIAS_PAIS.get(p, p)


def palavras(nome):
    return nome_norm(nome).split()


SIGLAS_CLUBE = {"fc", "cf", "ec", "sc", "se", "sl", "ad", "ca", "cr", "club", "de", "sp", "fk", "afc", "ac", "as", "rb", "sd"}


def mesmo_clube(a, b):
    """'Liverpool' e 'FC Liverpool' são o mesmo clube: compara as palavras sem as siglas."""
    ta = {t for t in pd._norm(a).split() if t not in SIGLAS_CLUBE}
    tb = {t for t in pd._norm(b).split() if t not in SIGLAS_CLUBE}
    if not ta or not tb:
        return False
    return ta <= tb or tb <= ta


def idade_ok(ano_copa, idade_copa, idade_atual):
    """Compara o ano de nascimento estimado pelos dois lados."""
    try:
        nasc_copa = int(ano_copa) - int(idade_copa)
        nasc_tm = ANO_REF - int(idade_atual)
    except (TypeError, ValueError):
        return True            # sem idade: não descarta, só não ajuda
    return abs(nasc_copa - nasc_tm) <= TOLERANCIA_IDADE


def casar(copa, candidatos_por_pais):
    """Devolve (id_tm, metodo, lista_de_candidatos). id_tm vazio se não casou."""
    nome = copa[0]
    pais = pais_do_copa(copa[1])
    ano, idade_copa = copa[2], copa[4]
    clube_copa = copa[6] if len(copa) > 6 else ""
    cand = candidatos_por_pais.get(pais, [])
    pal = palavras(nome)
    if not pal or not cand:
        return "", "sem candidato", []

    def filtrar(lista):
        return [c for c in lista if idade_ok(ano, idade_copa, c[3])]

    def desempatar(lista, metodo):
        """Se sobrar mais de um, fica com o que tem o mesmo clube da Copa (único)."""
        if len(lista) <= 1 or not clube_copa:
            return lista, metodo
        mesmo = [c for c in lista if mesmo_clube(c[1], clube_copa)]
        if len(mesmo) == 1:
            return mesmo, metodo + "+clube"
        return lista, metodo

    # 2. exato
    exato = [c for c in cand if nome_norm(c[0]) == nome_norm(nome)]
    ex = filtrar(exato)
    ex, m = desempatar(ex, "exato")
    if len(ex) == 1:
        return ex[0][7], m, ex
    if len(ex) > 1:
        return "", "ambíguo (exato)", ex

    # 3. parcial: palavras do nome mais curto contidas no outro
    parc = []
    for c in cand:
        pc = palavras(c[0])
        if not pc:
            continue
        curto, longo = (pal, pc) if len(pal) <= len(pc) else (pc, pal)
        if set(curto) <= set(longo):
            parc.append(c)
    parc = filtrar(parc)
    parc, m = desempatar(parc, "parcial")
    if len(parc) == 1:
        return parc[0][7], m, parc
    if len(parc) > 1:
        return "", "ambíguo (parcial)", parc

    # 4. primeiro + último nome iguais
    if len(pal) >= 2:
        sob = [c for c in cand
               if len(palavras(c[0])) >= 2 and palavras(c[0])[0] == pal[0] and palavras(c[0])[-1] == pal[-1]]
        sob = filtrar(sob)
        sob, m = desempatar(sob, "primeiro+último")
        if len(sob) == 1:
            return sob[0][7], m, sob
        if len(sob) > 1:
            return "", "ambíguo (primeiro+último)", sob

    return "", "não encontrado", []


def main():
    ap = argparse.ArgumentParser(description="Cruza copas.js (oGol) com dados.txt (Transfermarkt)")
    ap.add_argument("--copas", default="copas.js")
    ap.add_argument("--dados", default="dados.txt")
    ap.add_argument("--manual", default="ids_copa.txt")
    ap.add_argument("--saida", default="copas_tm.json")
    ap.add_argument("--csv", default="cruzamento_copa.csv", help="relatório para revisar os casos")
    args = ap.parse_args()

    copas = carregar_copas(args.copas)
    manual = carregar_manual(args.manual)

    # dados.txt: índice por país normalizado. Campos: 0 nome, 1 clube, 3 idade, 7 id, 10 nacionalidade
    cand = defaultdict(list)
    for linha in pd.ler_linhas_dados(args.dados):
        c = linha.split(",")
        if len(c) < 11 or not c[7]:
            continue
        cand[pd._pais(c[10])].append(c)
    dados_por_id = {c[7]: c for lst in cand.values() for c in lst}

    # um registro por jogador do oGol: usa a Copa mais recente (nome, país, idade mais recentes)
    mais_recente = {}
    for r in copas:
        pid = str(r[7])
        if pid not in mais_recente or int(r[2]) > int(mais_recente[pid][2]):
            mais_recente[pid] = r

    resultado, linhas_csv = {}, []
    contagem = defaultdict(int)
    for pid, r in mais_recente.items():
        if pid in manual:
            tm, metodo, lista = manual[pid], "manual", []
        else:
            tm, metodo, lista = casar(r, cand)
        contagem[metodo.split(" ")[0]] += 1
        if tm:
            resultado[pid] = {"tm": tm, "m": metodo}
        linhas_csv.append([pid, r[0], r[1], r[2], metodo, tm,
                           dados_por_id.get(tm, [""])[0] if tm else "",
                           "; ".join(f"{c[0]} ({c[1]}, {c[7]})" for c in lista[:4])])

    with open(args.saida, "w", encoding="utf-8") as f:
        json.dump({"v": 1, "rows": resultado}, f, ensure_ascii=False, separators=(",", ":"))

    # grava o ID do Transfermarkt no campo 11 de cada linha do copas.json/copas.js (usado pelo index e pelo modo Copa)
    atualizados = 0
    for r in copas:
        if len(r) < 12:
            r.extend([""] * (12 - len(r)))
        tm = resultado.get(str(r[7]), {}).get("tm", "")
        if r[11] != tm:
            r[11] = tm
            atualizados += 1
    txt = json.dumps({"v": 2, "rows": copas}, ensure_ascii=False, separators=(",", ":"))
    with open("copas.json", "w", encoding="utf-8") as f:
        f.write(txt)
    with open("copas.js", "w", encoding="utf-8") as f:
        f.write("window.COPAS_DATA=" + txt + ";")
    print(f"ID do Transfermarkt gravado no copas.json/copas.js ({atualizados} linhas atualizadas).")
    with open(args.csv, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["id_ogol", "nome_copa", "pais", "ano", "metodo", "id_tm", "nome_tm", "candidatos"])
        w.writerows(linhas_csv)

    total = len(mais_recente)
    casados = len(resultado)
    print(f"Jogadores únicos no copas: {total}")
    print(f"Casados: {casados} ({casados / total:.0%})")
    for m, n in sorted(contagem.items(), key=lambda x: -x[1]):
        print(f"  {m:18} {n}")
    print(f"\n{args.saida}: {casados} ids gravados. Revise {args.csv} (ambíguos e não encontrados).")
    print("Para corrigir um caso, acrescente 'ID_oGol ID_TM  # nome' em ids_copa.txt e rode de novo.")


if __name__ == "__main__":
    sys.exit(main())
