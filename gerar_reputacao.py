"""Gera o reputacao_clubes.json: reputacoes reais dos clubes para o jogo.

Le os clubes do dados.js (nomes e ligas vindos do Transfermarkt via pegar_dados.py)
e casa com a base extraida do site do Copero (copero-times.json). Os nomes passam
pelo mesmo encurtamento do jogo (funcao short(): "SC Corinthians" -> "Corinthians"),
porque e assim que o index.html guarda os clubes. Para cada clube
casado grava (chave = nome|liga, porque ha homonimos em divisoes diferentes):

    "Nome do clube|LIGA": [internacional, domestica, continental, divisao]

O jogo (index.html) carrega esse arquivo no inicio (REP_OVERRIDE) e usa essas
reputacoes no lugar das estimativas; clube fora da lista continua na estimativa.
Sem elas o jogo dava reputacao continental alta demais para clubes medios
(ex.: Stade Rennais e Troyes ganhando Champions League).

Uso (na pasta do jogo):
  python gerar_reputacao.py            # relatorio + grava o reputacao_clubes.json
  python gerar_reputacao.py --listar   # lista todos os casamentos (conferencia)
  python gerar_reputacao.py --seco     # so o relatorio, sem gravar
"""
import argparse
import json
import os
import re
import sys
import unicodedata

AQUI = os.path.dirname(os.path.abspath(__file__))
ARQ_JOGO = os.path.join(AQUI, "dados.js")
ARQ_COPERO = os.path.join(AQUI, "copero-times.json")
ARQ_SAIDA = os.path.join(AQUI, "reputacao_clubes.json")

LIMIAR_BOM = 0.80       # a partir daqui o casamento entra no arquivo
LIMIAR_DUVIDA = 0.62    # entre duvida e bom: aparece no relatorio para revisao
MIN_CASADOS = 250       # trava de seguranca: menos que isso = algo deu errado

# Palavras que nao ajudam a identificar o clube (mesma lista usada no _rea_copero)
PARADAS = {
    "fc", "cf", "ca", "cd", "sc", "ec", "se", "cr", "aa", "ad", "ac", "fk",
    "sk", "as", "ss", "ssc", "acf", "rb", "sv", "vfb", "vfl", "tsg", "sg",
    "rc", "rcd", "ud", "gd", "krc", "kaa", "kv", "rsc", "cs", "club", "de",
    "do", "da", "del", "la", "el", "los", "of", "s", "clube",
}

# Letras que o NFKD nao separa (dinamarques, turco etc.)
LETRAS = str.maketrans({"ø": "o", "æ": "ae", "ß": "ss", "ı": "i", "ł": "l",
                        "đ": "d", "ð": "d", "þ": "th", "œ": "oe"})

# Nomes que as bases escrevem diferente (chave = nome do dados.js ja normalizado)
ALIASES = {
    "olympique marselha": "Olympique de Marseille",
    "inter milao": "Inter",
    "copenhague": "F.C. Copenhagen",
    "royal antuerpia": "Royal Antwerp FC",
    "vv st truiden": "Sint-Truidense VV",
    "spartak moscou": "Spartak Moscow",
    "dinamo moscou": "Dynamo Moscow",
    "dinamo makhachkala": "Dynamo Makhachkala",
    "fackel voronezh": "Fakel",
    "operario fec": "Operário Ferroviário",
    "atlas guadalajara": "Atlas",
    "deportivo alaves": "Alaves",
    "shenzhen peng city": "Shenzhen Xinpengcheng",
    "zenit sao petersburgo": "Zenit San Petesburgo",
    "asteras aktor": "Asteras Tripolis",
    "rio negro aguilas": "Águilas Doradas",
    "rionegro aguilas": "Águilas Doradas",
    "central cordoba sde": "Central Córdoba de Santiago del Estero",
    "sporting cp": "Sporting Lisboa",
    "crb": "Club de Regatas de Brasil",
    "instituto acc": "Instituto de Córdoba",
    "west bromwich albion": "West Brom",
}

# Ligas do jogo que nao existem na base do Copero (para a regra de pais)
PAIS_EXTRA = {"L1": "GER", "QSL": "QAT", "BRA3": "BRA"}

# (nome normalizado, liga): NAO casar - casaria com um clube errado
EXCECOES = {
    ("internacional limeira", None),   # Serie C; "Club Nacional" tem nome parecido
    ("barra", None),                   # "Barra FC" ~ "Barracas Central" (ARG)
    ("1 colonia", None), ("colonia", None),   # Colonia (ALE): Copero nao tem liga alema
    ("botafogo", "BRA3"),              # Botafogo-PB (Serie C) x Botafogo-SP (Serie B)
}


def sem_acento(s):
    s = unicodedata.normalize("NFKD", str(s or "")).translate(LETRAS)
    return "".join(c for c in s if not unicodedata.combining(c))


def normaliza(s, com_paradas=True):
    s = sem_acento(s).lower().replace("&", " e ")
    s = re.sub(r"[^a-z0-9]+", " ", s)
    toks = [t for t in s.split() if t and not (com_paradas and t in PARADAS)]
    return " ".join(toks)


def _singular(t):
    # "hearts" -> "heart"; plurais simples (menos palavras terminadas em ss)
    return t[:-1] if len(t) > 4 and t.endswith("s") and not t.endswith("ss") else t


def tokens(s):
    n = normaliza(s)
    base = n.split()
    if not base or len("".join(base)) < 3:
        base = normaliza(s, com_paradas=False).split()
    return [_singular(t) for t in base]


def _parecido(t, outro):
    if t == outro:
        return True
    if min(len(t), len(outro)) >= 4 and (t.startswith(outro) or outro.startswith(t)):
        return True
    if min(len(t), len(outro)) >= 5:                      # fackel x fakel
        import difflib
        return difflib.SequenceMatcher(None, t, outro).ratio() >= 0.82
    return False


def similaridade(a, b):
    """0 = nada a ver, 1 = mesmo nome. Compara por tokens, nao por letra."""
    la, lb = tokens(a), tokens(b)
    ta, tb = set(la), set(lb)
    if not ta or not tb:
        return 0.0
    if "".join(la) == "".join(lb):        # "D.C. United" x "DC United"
        return 1.0
    na, nb = " ".join(sorted(ta)), " ".join(sorted(tb))
    if na == nb:
        return 1.0
    # nomes de uma palavra so: exigem quase-igualdade ("Anapolis" x "Napoli" nao vale)
    if len(ta) == 1 and len(tb) == 1:
        t, o = next(iter(ta)), next(iter(tb))
        import difflib
        return 0.9 if _parecido(t, o) and difflib.SequenceMatcher(None, t, o).ratio() >= 0.95 else 0.0
    # um nome contido no outro ("paris saint germain" x "... saint germain fc")
    if ta <= tb or tb <= ta:
        return 0.85
    if len(na) >= 5 and len(nb) >= 5 and (na in nb or nb in na):
        return 0.9
    comuns = {t for t in ta if any(_parecido(t, o) for o in tb)}
    return len(comuns) / len(ta | tb)


# Prefixos/sufixos que o index.html tira dos nomes (funcao short())
_RE_PREFIXO = re.compile(r"^(SE|CR|SC|EC|CA|AA|AD|CS|SER|RB|FC|AC|AS|SS|SSC|US|CF|UD|RC|SV|VfB|VfL) ")
_RE_SUFIXO = re.compile(r" (FC|EC|SC)$")


def curto(nome):
    """Mesmo encurtamento de nomes do index.html (o jogo guarda esse nome)."""
    return _RE_SUFIXO.sub("", _RE_PREFIXO.sub("", str(nome or "").strip()))


def clubes_do_jogo():
    """(nome curto do jogo, liga) unicos do dados.js com a contagem de jogadores."""
    t = open(ARQ_JOGO, encoding="utf-8", errors="replace").read()
    m = re.search(r"const DATA=`(.*?)`", t, re.S)
    if not m:
        sys.exit("ERRO: nao achei a lista de jogadores (const DATA) no dados.js")
    brutos = {}
    for linha in m.group(1).split(";"):
        p = linha.split(",")
        if len(p) < 14:
            continue
        brutos.setdefault((p[1], p[6]), 0)
        brutos[(p[1], p[6])] += 1
    clubes, origens = {}, {}
    for (bruto, liga), qtd in brutos.items():
        cur = curto(bruto)
        origens.setdefault((cur, liga), set()).add(bruto)
        clubes[(cur, liga)] = clubes.get((cur, liga), 0) + qtd
    colisoes = [(k, sorted(v)) for k, v in origens.items() if len(v) > 1]
    if colisoes:
        print("AVISO: nomes que o jogo junta no mesmo clube (short()):")
        for (n, l), orig in colisoes[:20]:
            print("   %-30s %-6s <- %s" % (n, l, ", ".join(orig)))
    return clubes


def base_copero():
    if not os.path.exists(ARQ_COPERO):
        sys.exit("ERRO: %s nao existe (base extraida do Copero)." % ARQ_COPERO)
    d = json.load(open(ARQ_COPERO, encoding="utf-8"))
    pais_da_liga = {lg["code"]: lg.get("pais") for lg in d.get("ligas", []) if lg.get("code")}
    pais_da_liga.update(PAIS_EXTRA)
    times = [t for t in d.get("times", [])
             if t.get("name") and t.get("gameCode") is not None]
    for t in times:
        t["pais"] = pais_da_liga.get(t["gameCode"])
    return times, pais_da_liga


def melhor_casamento(nome, liga, pais_jogo, por_liga, todos):
    """Melhor clube do Copero para o nome do jogo (com bonus de liga igual).

    Clubes de outro pais so casam se o nome bater exatamente (evita
    "Guarani FC" (BRA) casar com "Club Guaraní" (PAR) e parecidos).
    """
    alvo = ALIASES.get(normaliza(nome), nome)
    candidatos = list(por_liga.get(liga, [])) + [c for c in todos if c.get("gameCode") != liga]
    avaliados = []
    for c in candidatos:
        s = similaridade(alvo, c["name"])
        if c.get("short"):
            # o apelido so reforca quem ja tem alguma semelhanca no nome completo
            ss = 0.97 * similaridade(alvo, c["short"])
            if ss > s and s >= 0.6:
                s = ss
        if pais_jogo and c.get("pais") and c["pais"] != pais_jogo:
            continue                     # outro pais: nao casa
        if liga and c.get("gameCode") == liga:
            s += 0.08                    # mesma liga desempata homonimos
        if s > 0:
            avaliados.append((s, c))
    avaliados.sort(key=lambda x: (-x[0], x[1]["name"]))
    return avaliados[:3]


def main():
    ap = argparse.ArgumentParser(description="Gera o reputacao_clubes.json (base do Copero)")
    ap.add_argument("--seco", action="store_true", help="so mostra o relatorio")
    ap.add_argument("--listar", action="store_true", help="lista todos os casamentos")
    ap.add_argument("--forcar", action="store_true", help="grava mesmo com poucos casamentos")
    a = ap.parse_args()

    clubes = clubes_do_jogo()
    copero, pais_da_liga = base_copero()
    por_liga = {}
    for c in copero:
        por_liga.setdefault(c["gameCode"], []).append(c)
    print("clubes no jogo: %d | clubes no Copero: %d" % (len(clubes), len(copero)))

    casados, duvidosos, sem = {}, [], []
    for (nome, liga) in sorted(clubes):
        if (normaliza(nome), None) in EXCECOES or (normaliza(nome), liga) in EXCECOES:
            sem.append((nome, liga)); continue
        top = melhor_casamento(nome, liga, pais_da_liga.get(liga), por_liga, copero)
        if not top:
            sem.append((nome, liga)); continue
        s, c = top[0]
        seg = top[1][0] if len(top) > 1 else 0.0
        if s >= LIMIAR_BOM and (s - seg >= 0.05 or (len(top) > 1 and top[1][1]["name"] == c["name"])):
            chave = "%s|%s" % (nome, liga)     # nome|liga: evita homonimo em outra divisao
            casados[chave] = [c["rep"], c["repDom"], c["repCont"], c["tier"]]
            if a.listar:
                print("  %-34s -> %-32s %s (%.2f)" % (nome[:34], c["name"][:32], liga, min(s, 1.0)))
        elif s >= LIMIAR_DUVIDA:
            duvidosos.append((nome, liga, c["name"], min(s, 1.0), min(seg, 1.0)))
        else:
            sem.append((nome, liga))

    print("\ncasados: %d | duvidosos: %d | sem par: %d" % (len(casados), len(duvidosos), len(sem)))

    if duvidosos:
        print("\n--- duvidosos (%d): nome do jogo ~ candidato (nota | 2a opcao) ---" % len(duvidosos))
        for nome, liga, cand, s, seg in sorted(duvidosos, key=lambda x: -x[3])[:40]:
            print("  %-34s ~ %-32s %s (%.2f | %.2f)" % (nome[:34], cand[:32], liga, s, seg))

    if sem:
        print("\n--- sem par (%d) ---" % len(sem))
        for nome, liga in sem[:60]:
            print("  %-34s %s" % (nome[:34], liga))

    if a.seco:
        print("\n(--seco: nada foi gravado)")
        return
    if len(casados) < MIN_CASADOS and not a.forcar:
        sys.exit("\nERRO: so %d clubes casaram (minimo %d). Nao vou gravar; use --forcar se for certo."
                 % (len(casados), MIN_CASADOS))

    ordenado = {k: casados[k] for k in sorted(casados)}
    linhas = ",\n".join(" %s: [%s]" % (json.dumps(k, ensure_ascii=False),
                                       ",".join(str(v) for v in ordenado[k]))
                        for k in ordenado)
    with open(ARQ_SAIDA, "w", encoding="utf-8", newline="\n") as f:
        f.write("{\n" + linhas + "\n}\n")
    print("\ngravado: %s (%d clubes)" % (os.path.basename(ARQ_SAIDA), len(casados)))


if __name__ == "__main__":
    main()
