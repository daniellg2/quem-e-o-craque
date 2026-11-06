/* Série D 2026: cadastro exclusivo da carreira; fontes e escudos registrados abaixo. */
(function (global) {
  'use strict';
  const metadata={
  "season": 2026,
  "requestedSource": "https://www.transfermarkt.com.br/campeonato-brasileiro-serie-d/teilnehmer/pokalwettbewerb/BRA4",
  "source": "https://candangol.com.br/campeonatos/brasileirao-serie-d/2026/times",
  "reference": "https://www.cbf.com.br/futebol-brasileiro/noticias/undefined/caxias-x-londrina/cbf-divulga-grupos-da-serie-d-de-2026",
  "reputationNote": "Balanceamento do simulador: internacional 0 para os 12 clubes tradicionais listados; -1 para os demais. Doméstica e continental 0. Não são notas do Transfermarkt."
};
  // Paletas calculadas por corDoEscudo (index.html); recalcular quando os escudos forem substituídos.
  const teams=[
  {
    "c": "ABC",
    "slug": "abc",
    "sourceName": "ABC",
    "group": "A8",
    "rep": 0,
    "logo": "assets/database/crests/serie-d-2026/abc.png",
    "sourceLogo": "https://assets.candangol.com.br/cdn-cgi/image/width=128,quality=78,format=auto/teams/abc/abc.webp",
    "palette": {
      "top": "rgb(43,43,43)",
      "bot": "rgb(19,19,19)",
      "txt": "#fff"
    }
  },
  {
    "c": "ABECAT",
    "slug": "abecat",
    "sourceName": "ABECAT Ouvidorense",
    "group": "A11",
    "rep": -1,
    "logo": "assets/database/crests/serie-d-2026/abecat.png",
    "sourceLogo": "https://assets.candangol.com.br/cdn-cgi/image/width=128,quality=78,format=auto/teams/abecat/abecat.webp",
    "palette": {
      "top": "rgb(205,79,27)",
      "bot": "rgb(90,35,12)",
      "txt": "#fff"
    }
  },
  {
    "c": "Água Santa",
    "slug": "agua-santa",
    "sourceName": "Água Santa",
    "group": "A13",
    "rep": -1,
    "logo": "assets/database/crests/serie-d-2026/agua-santa.png",
    "sourceLogo": "https://assets.candangol.com.br/cdn-cgi/image/width=128,quality=78,format=auto/teams/agua-santa/agua-santa.webp",
    "palette": {
      "top": "rgb(14,33,71)",
      "bot": "rgb(6,15,31)",
      "txt": "#fff"
    }
  },
  {
    "c": "Águia de Marabá",
    "slug": "aguia-de-maraba",
    "sourceName": "Águia de Marabá",
    "group": "A5",
    "rep": -1,
    "logo": "assets/database/crests/serie-d-2026/aguia-de-maraba.png",
    "sourceLogo": "https://assets.candangol.com.br/cdn-cgi/image/width=128,quality=78,format=auto/teams/aguia-de-maraba/aguia-de-maraba.webp",
    "palette": {
      "top": "rgb(185,48,57)",
      "bot": "rgb(82,21,25)",
      "txt": "#fff"
    }
  },
  {
    "c": "Altos",
    "slug": "altos",
    "sourceName": "Altos",
    "group": "A7",
    "rep": -1,
    "logo": "assets/database/crests/serie-d-2026/altos.png",
    "sourceLogo": "https://assets.candangol.com.br/cdn-cgi/image/width=128,quality=78,format=auto/teams/altos/altos.webp",
    "palette": {
      "top": "rgb(14,140,80)",
      "bot": "rgb(6,62,36)",
      "txt": "#fff"
    }
  },
  {
    "c": "America-RJ",
    "slug": "america-rj",
    "sourceName": "America-RJ",
    "group": "A13",
    "rep": -1,
    "logo": "assets/database/crests/serie-d-2026/america-rj.png",
    "sourceLogo": "https://assets.candangol.com.br/cdn-cgi/image/width=128,quality=78,format=auto/teams/america-rj/america-rj.webp",
    "palette": {
      "top": "rgb(194,37,79)",
      "bot": "rgb(86,16,35)",
      "txt": "#fff"
    }
  },
  {
    "c": "América-RN",
    "slug": "america-rn",
    "sourceName": "América-RN",
    "group": "A8",
    "rep": 0,
    "logo": "assets/database/crests/serie-d-2026/america-rn.png",
    "sourceLogo": "https://assets.candangol.com.br/cdn-cgi/image/width=128,quality=78,format=auto/teams/america-rn/america-rn.webp",
    "palette": {
      "top": "rgb(242,55,43)",
      "bot": "rgb(107,24,19)",
      "txt": "#fff"
    }
  },
  {
    "c": "Aparecidense",
    "slug": "aparecidense",
    "sourceName": "Aparecidense",
    "group": "A3",
    "rep": -1,
    "logo": "assets/database/crests/serie-d-2026/aparecidense.png",
    "sourceLogo": "https://assets.candangol.com.br/cdn-cgi/image/width=128,quality=78,format=auto/teams/aparecidense/aparecidense.webp",
    "palette": {
      "top": "rgb(167,160,62)",
      "bot": "rgb(74,71,27)",
      "txt": "#fff"
    }
  },
  {
    "c": "Araguaína",
    "slug": "araguaina",
    "sourceName": "Araguaína",
    "group": "A2",
    "rep": -1,
    "logo": "assets/database/crests/serie-d-2026/araguaina.png",
    "sourceLogo": "https://assets.candangol.com.br/cdn-cgi/image/width=128,quality=78,format=auto/teams/araguaina/araguaina.webp",
    "palette": {
      "top": "rgb(14,137,200)",
      "bot": "rgb(6,61,88)",
      "txt": "#fff"
    }
  },
  {
    "c": "ASA",
    "slug": "asa-arapiraca",
    "sourceName": "ASA",
    "group": "A10",
    "rep": -1,
    "logo": "assets/database/crests/serie-d-2026/asa-arapiraca.png",
    "sourceLogo": "https://assets.candangol.com.br/cdn-cgi/image/width=128,quality=78,format=auto/teams/asa-arapiraca/asa-arapiraca.webp",
    "palette": {
      "top": "rgb(43,43,43)",
      "bot": "rgb(19,19,19)",
      "txt": "#fff"
    }
  },
  {
    "c": "Atlético Cearense",
    "slug": "atletico-ce",
    "sourceName": "Atlético Cearense",
    "group": "A7",
    "rep": -1,
    "logo": "assets/database/crests/serie-d-2026/atletico-ce.png",
    "sourceLogo": "https://assets.candangol.com.br/cdn-cgi/image/width=128,quality=78,format=auto/teams/atletico-ce/atletico-ce.webp",
    "palette": {
      "top": "rgb(158,67,65)",
      "bot": "rgb(70,30,29)",
      "txt": "#fff"
    }
  },
  {
    "c": "Atlético-BA",
    "slug": "atletico-de-alagoinhas",
    "sourceName": "Atlético de Alagoinhas",
    "group": "A10",
    "rep": -1,
    "logo": "assets/database/crests/serie-d-2026/atletico-de-alagoinhas.png",
    "sourceLogo": "https://assets.candangol.com.br/cdn-cgi/image/width=128,quality=78,format=auto/teams/atletico-de-alagoinhas/atletico-de-alagoinhas.webp",
    "palette": {
      "top": "rgb(242,33,32)",
      "bot": "rgb(107,14,14)",
      "txt": "#fff"
    }
  },
  {
    "c": "Azuriz",
    "slug": "azuriz",
    "sourceName": "Azuriz",
    "group": "A16",
    "rep": -1,
    "logo": "assets/database/crests/serie-d-2026/azuriz.png",
    "sourceLogo": "https://assets.candangol.com.br/cdn-cgi/image/width=128,quality=78,format=auto/teams/azuriz/azuriz.webp",
    "palette": {
      "top": "rgb(42,95,138)",
      "bot": "rgb(19,42,61)",
      "txt": "#fff"
    }
  },
  {
    "c": "Betim",
    "slug": "betim",
    "sourceName": "Betim",
    "group": "A11",
    "rep": -1,
    "logo": "assets/database/crests/serie-d-2026/betim.png",
    "sourceLogo": "https://assets.candangol.com.br/cdn-cgi/image/width=128,quality=78,format=auto/teams/betim/betim.webp",
    "palette": {
      "top": "rgb(122,29,31)",
      "bot": "rgb(54,13,14)",
      "txt": "#fff"
    }
  },
  {
    "c": "Blumenau",
    "slug": "blumenau",
    "sourceName": "Blumenau",
    "group": "A16",
    "rep": -1,
    "logo": "assets/database/crests/serie-d-2026/blumenau.png",
    "sourceLogo": "https://assets.candangol.com.br/cdn-cgi/image/width=128,quality=78,format=auto/teams/blumenau/blumenau.webp",
    "palette": {
      "top": "rgb(111,18,42)",
      "bot": "rgb(49,8,19)",
      "txt": "#fff"
    }
  },
  {
    "c": "Brasil de Pelotas",
    "slug": "brasil-de-pelotas",
    "sourceName": "Brasil de Pelotas",
    "group": "A16",
    "rep": 0,
    "logo": "assets/database/crests/serie-d-2026/brasil-de-pelotas.png",
    "sourceLogo": "https://assets.candangol.com.br/cdn-cgi/image/width=128,quality=78,format=auto/teams/brasil-de-pelotas/brasil-de-pelotas.webp",
    "palette": {
      "top": "rgb(166,8,33)",
      "bot": "rgb(73,4,15)",
      "txt": "#fff"
    }
  },
  {
    "c": "Brasiliense",
    "slug": "brasiliense",
    "sourceName": "Brasiliense S.A.F",
    "group": "A3",
    "rep": 0,
    "logo": "assets/database/crests/serie-d-2026/brasiliense.png",
    "sourceLogo": "https://assets.candangol.com.br/cdn-cgi/image/width=128,quality=78,format=auto/teams/brasiliense/Brasiliense-2010-01-02_current.webp",
    "palette": {
      "top": "rgb(184,167,9)",
      "bot": "rgb(97,88,5)",
      "txt": "#fff"
    }
  },
  {
    "c": "Capital-DF",
    "slug": "capital",
    "sourceName": "Capital SAF",
    "group": "A4",
    "rep": -1,
    "logo": "assets/database/crests/serie-d-2026/capital.png",
    "sourceLogo": "https://assets.candangol.com.br/cdn-cgi/image/width=128,quality=78,format=auto/teams/capital/Capital-2024-02-14_current.webp",
    "palette": {
      "top": "rgb(13,142,190)",
      "bot": "rgb(6,63,84)",
      "txt": "#fff"
    }
  },
  {
    "c": "Cascavel",
    "slug": "cascavel",
    "sourceName": "Cascavel",
    "group": "A15",
    "rep": -1,
    "logo": "assets/database/crests/serie-d-2026/cascavel.png",
    "sourceLogo": "https://assets.candangol.com.br/cdn-cgi/image/width=128,quality=78,format=auto/teams/cascavel/cascavel.webp",
    "palette": {
      "top": "rgb(189,180,7)",
      "bot": "rgb(83,80,3)",
      "txt": "#fff"
    }
  },
  {
    "c": "Ceilândia",
    "slug": "ceilandia",
    "sourceName": "Ceilândia",
    "group": "A4",
    "rep": -1,
    "logo": "assets/database/crests/serie-d-2026/ceilandia.png",
    "sourceLogo": "https://assets.candangol.com.br/cdn-cgi/image/width=128,quality=78,format=auto/teams/ceilandia/Ceilandia-2022-01-01_current.webp",
    "palette": {
      "top": "rgb(149,127,91)",
      "bot": "rgb(66,56,40)",
      "txt": "#fff"
    }
  },
  {
    "c": "Central",
    "slug": "central-sc",
    "sourceName": "Central",
    "group": "A8",
    "rep": -1,
    "logo": "assets/database/crests/serie-d-2026/central-sc.png",
    "sourceLogo": "https://assets.candangol.com.br/cdn-cgi/image/width=128,quality=78,format=auto/teams/central-sc/central-sc.webp",
    "palette": {
      "top": "rgb(133,133,133)",
      "bot": "rgb(59,59,59)",
      "txt": "#fff"
    }
  },
  {
    "c": "Cianorte",
    "slug": "cianorte",
    "sourceName": "Cianorte",
    "group": "A15",
    "rep": -1,
    "logo": "assets/database/crests/serie-d-2026/cianorte.png",
    "sourceLogo": "https://assets.candangol.com.br/cdn-cgi/image/width=128,quality=78,format=auto/teams/cianorte/cianorte.webp",
    "palette": {
      "top": "rgb(43,47,92)",
      "bot": "rgb(19,21,41)",
      "txt": "#fff"
    }
  },
  {
    "c": "CRAC",
    "slug": "crac",
    "sourceName": "CRAC",
    "group": "A11",
    "rep": -1,
    "logo": "assets/database/crests/serie-d-2026/crac.png",
    "sourceLogo": "https://assets.candangol.com.br/cdn-cgi/image/width=128,quality=78,format=auto/teams/crac/crac.webp",
    "palette": {
      "top": "rgb(56,171,217)",
      "bot": "rgb(25,76,96)",
      "txt": "#fff"
    }
  },
  {
    "c": "CSA",
    "slug": "csa",
    "sourceName": "CSA",
    "group": "A10",
    "rep": 0,
    "logo": "assets/database/crests/serie-d-2026/csa.png",
    "sourceLogo": "https://assets.candangol.com.br/cdn-cgi/image/width=128,quality=78,format=auto/teams/csa/csa.webp",
    "palette": {
      "top": "rgb(14,37,94)",
      "bot": "rgb(6,17,41)",
      "txt": "#fff"
    }
  },
  {
    "c": "CSE",
    "slug": "cse",
    "sourceName": "CSE",
    "group": "A10",
    "rep": -1,
    "logo": "assets/database/crests/serie-d-2026/cse.png",
    "sourceLogo": "https://assets.candangol.com.br/cdn-cgi/image/width=128,quality=78,format=auto/teams/cse/cse.webp",
    "palette": {
      "top": "rgb(213,66,47)",
      "bot": "rgb(94,29,21)",
      "txt": "#fff"
    }
  },
  {
    "c": "Decisão",
    "slug": "decisao",
    "sourceName": "Decisão Goiana",
    "group": "A9",
    "rep": -1,
    "logo": "assets/database/crests/serie-d-2026/decisao.png",
    "sourceLogo": "https://assets.candangol.com.br/cdn-cgi/image/width=128,quality=78,format=auto/teams/decisao/decisao.webp",
    "palette": {
      "top": "rgb(26,72,121)",
      "bot": "rgb(12,32,53)",
      "txt": "#fff"
    }
  },
  {
    "c": "Democrata GV",
    "slug": "democrata-gv",
    "sourceName": "Democrata GV",
    "group": "A12",
    "rep": -1,
    "logo": "assets/database/crests/serie-d-2026/democrata-gv.png",
    "sourceLogo": "https://assets.candangol.com.br/cdn-cgi/image/width=128,quality=78,format=auto/teams/democrata-gv/democrata-gv.webp",
    "palette": {
      "top": "rgb(43,43,43)",
      "bot": "rgb(19,19,19)",
      "txt": "#fff"
    }
  },
  {
    "c": "Ferroviário",
    "slug": "ferroviario",
    "sourceName": "Ferroviário",
    "group": "A7",
    "rep": 0,
    "logo": "assets/database/crests/serie-d-2026/ferroviario.png",
    "sourceLogo": "https://assets.candangol.com.br/cdn-cgi/image/width=128,quality=78,format=auto/teams/ferroviario/ferroviario.webp",
    "palette": {
      "top": "rgb(242,8,7)",
      "bot": "rgb(107,3,3)",
      "txt": "#fff"
    }
  },
  {
    "c": "Fluminense-PI",
    "slug": "fluminense-pi",
    "sourceName": "Fluminense-PI",
    "group": "A7",
    "rep": -1,
    "logo": "assets/database/crests/serie-d-2026/fluminense-pi.png",
    "sourceLogo": "https://assets.candangol.com.br/cdn-cgi/image/width=128,quality=78,format=auto/teams/fluminense-pi/fluminense-pi.webp",
    "palette": {
      "top": "rgb(136,35,57)",
      "bot": "rgb(60,16,25)",
      "txt": "#fff"
    }
  },
  {
    "c": "Galvez",
    "slug": "galvez",
    "sourceName": "Galvez",
    "group": "A2",
    "rep": -1,
    "logo": "assets/database/crests/serie-d-2026/galvez.png",
    "sourceLogo": "https://assets.candangol.com.br/cdn-cgi/image/width=128,quality=78,format=auto/teams/galvez/galvez.webp",
    "palette": {
      "top": "rgb(203,192,2)",
      "bot": "rgb(106,101,1)",
      "txt": "#111"
    }
  },
  {
    "c": "Gama",
    "slug": "gama",
    "sourceName": "Gama",
    "group": "A3",
    "rep": 0,
    "logo": "assets/database/crests/serie-d-2026/gama.png",
    "sourceLogo": "https://assets.candangol.com.br/cdn-cgi/image/width=128,quality=78,format=auto/teams/gama/Gama-2003_current.webp",
    "palette": {
      "top": "rgb(25,113,87)",
      "bot": "rgb(11,50,38)",
      "txt": "#fff"
    }
  },
  {
    "c": "GAS",
    "slug": "gas",
    "sourceName": "Grêmio Atlético Sampaio",
    "group": "A1",
    "rep": -1,
    "logo": "assets/database/crests/serie-d-2026/gas.png",
    "sourceLogo": "https://assets.candangol.com.br/cdn-cgi/image/width=128,quality=78,format=auto/teams/gas/gas.webp",
    "palette": {
      "top": "rgb(238,22,2)",
      "bot": "rgb(105,10,1)",
      "txt": "#fff"
    }
  },
  {
    "c": "Goiatuba",
    "slug": "goiatuba",
    "sourceName": "Goiatuba",
    "group": "A4",
    "rep": -1,
    "logo": "assets/database/crests/serie-d-2026/goiatuba.png",
    "sourceLogo": "https://assets.candangol.com.br/cdn-cgi/image/width=128,quality=78,format=auto/teams/goiatuba/goiatuba.webp",
    "palette": {
      "top": "rgb(54,56,149)",
      "bot": "rgb(24,25,66)",
      "txt": "#fff"
    }
  },
  {
    "c": "Guaporé",
    "slug": "guapore",
    "sourceName": "Guaporé",
    "group": "A2",
    "rep": -1,
    "logo": "assets/database/crests/serie-d-2026/guapore.png",
    "sourceLogo": "https://assets.candangol.com.br/cdn-cgi/image/width=128,quality=78,format=auto/teams/guapore/guapore.webp",
    "palette": {
      "top": "rgb(223,123,25)",
      "bot": "rgb(99,54,11)",
      "txt": "#fff"
    }
  },
  {
    "c": "Guarany de Bagé",
    "slug": "guarany-de-bage",
    "sourceName": "Guarany de Bagé",
    "group": "A15",
    "rep": -1,
    "logo": "assets/database/crests/serie-d-2026/guarany-de-bage.png",
    "sourceLogo": "https://assets.candangol.com.br/cdn-cgi/image/width=128,quality=78,format=auto/teams/guarany-de-bage/guarany-de-bage.webp",
    "palette": {
      "top": "rgb(223,35,42)",
      "bot": "rgb(99,15,19)",
      "txt": "#fff"
    }
  },
  {
    "c": "Humaitá",
    "slug": "humaita",
    "sourceName": "Humaitá",
    "group": "A2",
    "rep": -1,
    "logo": "assets/database/crests/serie-d-2026/humaita.png",
    "sourceLogo": "https://assets.candangol.com.br/cdn-cgi/image/width=128,quality=78,format=auto/teams/humaita/humaita.webp",
    "palette": {
      "top": "rgb(233,6,17)",
      "bot": "rgb(103,3,8)",
      "txt": "#fff"
    }
  },
  {
    "c": "IAPE",
    "slug": "iape",
    "sourceName": "IAPE",
    "group": "A6",
    "rep": -1,
    "logo": "assets/database/crests/serie-d-2026/iape.png",
    "sourceLogo": "https://assets.candangol.com.br/cdn-cgi/image/width=128,quality=78,format=auto/teams/iape/iape.webp",
    "palette": {
      "top": "rgb(176,168,24)",
      "bot": "rgb(92,88,12)",
      "txt": "#fff"
    }
  },
  {
    "c": "Iguatu",
    "slug": "iguatu",
    "sourceName": "Iguatu",
    "group": "A6",
    "rep": -1,
    "logo": "assets/database/crests/serie-d-2026/iguatu.png",
    "sourceLogo": "https://assets.candangol.com.br/cdn-cgi/image/width=128,quality=78,format=auto/teams/iguatu/iguatu.webp",
    "palette": {
      "top": "rgb(35,52,190)",
      "bot": "rgb(16,23,84)",
      "txt": "#fff"
    }
  },
  {
    "c": "Imperatriz",
    "slug": "imperatriz",
    "sourceName": "Imperatriz",
    "group": "A5",
    "rep": -1,
    "logo": "assets/database/crests/serie-d-2026/imperatriz.png",
    "sourceLogo": "https://assets.candangol.com.br/cdn-cgi/image/width=128,quality=78,format=auto/teams/imperatriz/imperatriz.webp",
    "palette": {
      "top": "rgb(230,46,60)",
      "bot": "rgb(102,20,27)",
      "txt": "#fff"
    }
  },
  {
    "c": "Independência-AC",
    "slug": "independencia-ac",
    "sourceName": "Independência-AC",
    "group": "A2",
    "rep": -1,
    "logo": "assets/database/crests/serie-d-2026/independencia-ac.png",
    "sourceLogo": "https://assets.candangol.com.br/cdn-cgi/image/width=128,quality=78,format=auto/teams/independencia-ac/independencia-ac.webp",
    "palette": {
      "top": "rgb(210,54,47)",
      "bot": "rgb(93,24,21)",
      "txt": "#fff"
    }
  },
  {
    "c": "Inhumas",
    "slug": "inhumas",
    "sourceName": "Inhumas",
    "group": "A3",
    "rep": -1,
    "logo": "assets/database/crests/serie-d-2026/inhumas.png",
    "sourceLogo": "https://assets.candangol.com.br/cdn-cgi/image/width=128,quality=78,format=auto/teams/inhumas/inhumas.webp",
    "palette": {
      "top": "rgb(145,18,15)",
      "bot": "rgb(64,8,6)",
      "txt": "#fff"
    }
  },
  {
    "c": "Ivinhema",
    "slug": "ivinhema",
    "sourceName": "Ivinhema",
    "group": "A11",
    "rep": -1,
    "logo": "assets/database/crests/serie-d-2026/ivinhema.png",
    "sourceLogo": "https://assets.candangol.com.br/cdn-cgi/image/width=128,quality=78,format=auto/teams/ivinhema/ivinhema.webp",
    "palette": {
      "top": "rgb(15,137,201)",
      "bot": "rgb(7,61,89)",
      "txt": "#fff"
    }
  },
  {
    "c": "Jacuipense",
    "slug": "jacuipense",
    "sourceName": "Jacuipense",
    "group": "A10",
    "rep": -1,
    "logo": "assets/database/crests/serie-d-2026/jacuipense.png",
    "sourceLogo": "https://assets.candangol.com.br/cdn-cgi/image/width=128,quality=78,format=auto/teams/jacuipense/jacuipense.webp",
    "palette": {
      "top": "rgb(114,34,43)",
      "bot": "rgb(51,15,19)",
      "txt": "#fff"
    }
  },
  {
    "c": "Joinville",
    "slug": "joinville",
    "sourceName": "Joinville",
    "group": "A15",
    "rep": 0,
    "logo": "assets/database/crests/serie-d-2026/joinville.png",
    "sourceLogo": "https://assets.candangol.com.br/cdn-cgi/image/width=128,quality=78,format=auto/teams/joinville/joinville.webp",
    "palette": {
      "top": "rgb(222,67,64)",
      "bot": "rgb(98,30,28)",
      "txt": "#fff"
    }
  },
  {
    "c": "Juazeirense",
    "slug": "juazeirense",
    "sourceName": "Juazeirense",
    "group": "A10",
    "rep": -1,
    "logo": "assets/database/crests/serie-d-2026/juazeirense.png",
    "sourceLogo": "https://assets.candangol.com.br/cdn-cgi/image/width=128,quality=78,format=auto/teams/juazeirense/juazeirense.webp",
    "palette": {
      "top": "rgb(242,44,54)",
      "bot": "rgb(107,20,24)",
      "txt": "#fff"
    }
  },
  {
    "c": "Lagarto",
    "slug": "lagarto",
    "sourceName": "Lagarto",
    "group": "A9",
    "rep": -1,
    "logo": "assets/database/crests/serie-d-2026/lagarto.png",
    "sourceLogo": "https://assets.candangol.com.br/cdn-cgi/image/width=128,quality=78,format=auto/teams/lagarto/lagarto.webp",
    "palette": {
      "top": "rgb(239,17,18)",
      "bot": "rgb(106,7,8)",
      "txt": "#fff"
    }
  },
  {
    "c": "Laguna",
    "slug": "laguna",
    "sourceName": "Laguna",
    "group": "A8",
    "rep": -1,
    "logo": "assets/database/crests/serie-d-2026/laguna.png",
    "sourceLogo": "https://assets.candangol.com.br/cdn-cgi/image/width=128,quality=78,format=auto/teams/laguna/laguna.webp",
    "palette": {
      "top": "rgb(3,32,88)",
      "bot": "rgb(1,14,39)",
      "txt": "#fff"
    }
  },
  {
    "c": "Luverdense",
    "slug": "luverdense",
    "sourceName": "Luverdense",
    "group": "A3",
    "rep": -1,
    "logo": "assets/database/crests/serie-d-2026/luverdense.png",
    "sourceLogo": "https://assets.candangol.com.br/cdn-cgi/image/width=128,quality=78,format=auto/teams/luverdense/luverdense.webp",
    "palette": {
      "top": "rgb(61,86,40)",
      "bot": "rgb(27,38,17)",
      "txt": "#fff"
    }
  },
  {
    "c": "Madureira",
    "slug": "madureira",
    "sourceName": "Madureira",
    "group": "A13",
    "rep": -1,
    "logo": "assets/database/crests/serie-d-2026/madureira.png",
    "sourceLogo": "https://assets.candangol.com.br/cdn-cgi/image/width=128,quality=78,format=auto/teams/madureira/madureira.webp",
    "palette": {
      "top": "rgb(22,4,117)",
      "bot": "rgb(10,2,52)",
      "txt": "#fff"
    }
  },
  {
    "c": "Maguary",
    "slug": "maguary",
    "sourceName": "Maguary",
    "group": "A8",
    "rep": -1,
    "logo": "assets/database/crests/serie-d-2026/maguary.png",
    "sourceLogo": "https://assets.candangol.com.br/cdn-cgi/image/width=128,quality=78,format=auto/teams/maguary/maguary.webp",
    "palette": {
      "top": "rgb(16,87,150)",
      "bot": "rgb(7,38,66)",
      "txt": "#fff"
    }
  },
  {
    "c": "Manauara",
    "slug": "manauara",
    "sourceName": "Manauara",
    "group": "A1",
    "rep": -1,
    "logo": "assets/database/crests/serie-d-2026/manauara.png",
    "sourceLogo": "https://assets.candangol.com.br/cdn-cgi/image/width=128,quality=78,format=auto/teams/manauara/manauara.webp",
    "palette": {
      "top": "rgb(202,81,55)",
      "bot": "rgb(89,36,24)",
      "txt": "#fff"
    }
  },
  {
    "c": "Manaus",
    "slug": "manaus",
    "sourceName": "Manaus",
    "group": "A1",
    "rep": -1,
    "logo": "assets/database/crests/serie-d-2026/manaus.png",
    "sourceLogo": "https://assets.candangol.com.br/cdn-cgi/image/width=128,quality=78,format=auto/teams/manaus/manaus.webp",
    "palette": {
      "top": "rgb(8,135,62)",
      "bot": "rgb(4,60,28)",
      "txt": "#fff"
    }
  },
  {
    "c": "Maracanã",
    "slug": "maracana",
    "sourceName": "Maracanã",
    "group": "A6",
    "rep": -1,
    "logo": "assets/database/crests/serie-d-2026/maracana.png",
    "sourceLogo": "https://assets.candangol.com.br/cdn-cgi/image/width=128,quality=78,format=auto/teams/maracana/maracana.webp",
    "palette": {
      "top": "rgb(10,129,182)",
      "bot": "rgb(4,57,80)",
      "txt": "#fff"
    }
  },
  {
    "c": "Marcílio Dias",
    "slug": "marcilio-dias",
    "sourceName": "Marcílio Dias",
    "group": "A16",
    "rep": -1,
    "logo": "assets/database/crests/serie-d-2026/marcilio-dias.png",
    "sourceLogo": "https://assets.candangol.com.br/cdn-cgi/image/width=128,quality=78,format=auto/teams/marcilio-dias/marcilio-dias.webp",
    "palette": {
      "top": "rgb(40,39,113)",
      "bot": "rgb(18,17,50)",
      "txt": "#fff"
    }
  },
  {
    "c": "Maricá",
    "slug": "marica",
    "sourceName": "Maricá",
    "group": "A14",
    "rep": -1,
    "logo": "assets/database/crests/serie-d-2026/marica.png",
    "sourceLogo": "https://assets.candangol.com.br/cdn-cgi/image/width=128,quality=78,format=auto/teams/marica/marica.webp",
    "palette": {
      "top": "rgb(0,53,94)",
      "bot": "rgb(0,24,42)",
      "txt": "#fff"
    }
  },
  {
    "c": "Mixto",
    "slug": "mixto",
    "sourceName": "Mixto",
    "group": "A4",
    "rep": -1,
    "logo": "assets/database/crests/serie-d-2026/mixto.png",
    "sourceLogo": "https://assets.candangol.com.br/cdn-cgi/image/width=128,quality=78,format=auto/teams/mixto/mixto.webp",
    "palette": {
      "top": "rgb(43,43,43)",
      "bot": "rgb(19,19,19)",
      "txt": "#fff"
    }
  },
  {
    "c": "Monte Roraima",
    "slug": "monte-roraima",
    "sourceName": "Monte Roraima",
    "group": "A1",
    "rep": -1,
    "logo": "assets/database/crests/serie-d-2026/monte-roraima.png",
    "sourceLogo": "https://assets.candangol.com.br/cdn-cgi/image/width=128,quality=78,format=auto/teams/monte-roraima/monte-roraima.webp",
    "palette": {
      "top": "rgb(16,69,30)",
      "bot": "rgb(7,31,13)",
      "txt": "#fff"
    }
  },
  {
    "c": "Moto Club",
    "slug": "moto-club",
    "sourceName": "Moto Club",
    "group": "A6",
    "rep": -1,
    "logo": "assets/database/crests/serie-d-2026/moto-club.png",
    "sourceLogo": "https://assets.candangol.com.br/cdn-cgi/image/width=128,quality=78,format=auto/teams/moto-club/moto-club.webp",
    "palette": {
      "top": "rgb(195,2,1)",
      "bot": "rgb(86,1,0)",
      "txt": "#fff"
    }
  },
  {
    "c": "Nacional-AM",
    "slug": "nacional",
    "sourceName": "Nacional",
    "group": "A1",
    "rep": -1,
    "logo": "assets/database/crests/serie-d-2026/nacional.png",
    "sourceLogo": "https://assets.candangol.com.br/cdn-cgi/image/width=128,quality=78,format=auto/teams/nacional/nacional.webp",
    "palette": {
      "top": "rgb(196,173,20)",
      "bot": "rgb(103,91,11)",
      "txt": "#fff"
    }
  },
  {
    "c": "Noroeste",
    "slug": "noroeste",
    "sourceName": "Noroeste",
    "group": "A14",
    "rep": -1,
    "logo": "assets/database/crests/serie-d-2026/noroeste.png",
    "sourceLogo": "https://assets.candangol.com.br/cdn-cgi/image/width=128,quality=78,format=auto/teams/noroeste/noroeste.webp",
    "palette": {
      "top": "rgb(230,28,29)",
      "bot": "rgb(102,12,13)",
      "txt": "#fff"
    }
  },
  {
    "c": "Nova Iguaçu",
    "slug": "nova-iguacu",
    "sourceName": "Nova iguaçu",
    "group": "A14",
    "rep": -1,
    "logo": "assets/database/crests/serie-d-2026/nova-iguacu.png",
    "sourceLogo": "https://assets.candangol.com.br/cdn-cgi/image/width=128,quality=78,format=auto/teams/nova-iguacu/nova-iguacu.webp",
    "palette": {
      "top": "rgb(212,131,34)",
      "bot": "rgb(94,58,15)",
      "txt": "#fff"
    }
  },
  {
    "c": "Operário-MS",
    "slug": "operario-ms",
    "sourceName": "Operário-MS",
    "group": "A11",
    "rep": -1,
    "logo": "assets/database/crests/serie-d-2026/operario-ms.png",
    "sourceLogo": "https://assets.candangol.com.br/cdn-cgi/image/width=128,quality=78,format=auto/teams/operario-ms/operario-ms.webp",
    "palette": {
      "top": "rgb(133,133,133)",
      "bot": "rgb(59,59,59)",
      "txt": "#fff"
    }
  },
  {
    "c": "Operário-MT",
    "slug": "operario-vg",
    "sourceName": "Operario",
    "group": "A4",
    "rep": -1,
    "logo": "assets/database/crests/serie-d-2026/operario-vg.png",
    "sourceLogo": "https://assets.candangol.com.br/cdn-cgi/image/width=128,quality=78,format=auto/teams/operario-vg/operario-vg.webp",
    "palette": {
      "top": "rgb(12,101,56)",
      "bot": "rgb(5,45,25)",
      "txt": "#fff"
    }
  },
  {
    "c": "Oratório",
    "slug": "oratorio",
    "sourceName": "Oratório",
    "group": "A5",
    "rep": -1,
    "logo": "assets/database/crests/serie-d-2026/oratorio.png",
    "sourceLogo": "https://assets.candangol.com.br/cdn-cgi/image/width=128,quality=78,format=auto/teams/oratorio/oratorio.webp",
    "palette": {
      "top": "rgb(35,75,114)",
      "bot": "rgb(16,33,50)",
      "txt": "#fff"
    }
  },
  {
    "c": "Parnahyba",
    "slug": "parnahyba",
    "sourceName": "Parnahyba",
    "group": "A6",
    "rep": -1,
    "logo": "assets/database/crests/serie-d-2026/parnahyba.png",
    "sourceLogo": "https://assets.candangol.com.br/cdn-cgi/image/width=128,quality=78,format=auto/teams/parnahyba/parnahyba.webp",
    "palette": {
      "top": "rgb(35,50,96)",
      "bot": "rgb(16,22,43)",
      "txt": "#fff"
    }
  },
  {
    "c": "Piauí",
    "slug": "piaui",
    "sourceName": "Piauí",
    "group": "A7",
    "rep": -1,
    "logo": "assets/database/crests/serie-d-2026/piaui.png",
    "sourceLogo": "https://assets.candangol.com.br/cdn-cgi/image/width=128,quality=78,format=auto/teams/piaui/piaui.webp",
    "palette": {
      "top": "rgb(45,69,129)",
      "bot": "rgb(20,31,57)",
      "txt": "#fff"
    }
  },
  {
    "c": "Porto Velho",
    "slug": "porto-velho",
    "sourceName": "Porto Velho",
    "group": "A2",
    "rep": -1,
    "logo": "assets/database/crests/serie-d-2026/porto-velho.png",
    "sourceLogo": "https://assets.candangol.com.br/cdn-cgi/image/width=128,quality=78,format=auto/teams/porto-velho/porto-velho.webp",
    "palette": {
      "top": "rgb(33,46,106)",
      "bot": "rgb(14,20,47)",
      "txt": "#fff"
    }
  },
  {
    "c": "Porto-BA",
    "slug": "porto-ba",
    "sourceName": "Porto-BA",
    "group": "A12",
    "rep": -1,
    "logo": "assets/database/crests/serie-d-2026/porto-ba.png",
    "sourceLogo": "https://assets.candangol.com.br/cdn-cgi/image/width=128,quality=78,format=auto/teams/porto-ba/porto-ba.webp",
    "palette": {
      "top": "rgb(179,116,8)",
      "bot": "rgb(79,51,4)",
      "txt": "#fff"
    }
  },
  {
    "c": "Portuguesa-RJ",
    "slug": "portuguesa-rj",
    "sourceName": "Portuguesa-RJ",
    "group": "A13",
    "rep": -1,
    "logo": "assets/database/crests/serie-d-2026/portuguesa-rj.png",
    "sourceLogo": "https://assets.candangol.com.br/cdn-cgi/image/width=128,quality=78,format=auto/teams/portuguesa-rj/portuguesa-rj.webp",
    "palette": {
      "top": "rgb(15,151,60)",
      "bot": "rgb(6,67,26)",
      "txt": "#fff"
    }
  },
  {
    "c": "Portuguesa-SP",
    "slug": "portuguesa-sp",
    "sourceName": "Portuguesa-SP",
    "group": "A13",
    "rep": 0,
    "logo": "assets/database/crests/serie-d-2026/portuguesa-sp.png",
    "sourceLogo": "https://assets.candangol.com.br/cdn-cgi/image/width=128,quality=78,format=auto/teams/portuguesa-sp/portuguesa-sp.webp",
    "palette": {
      "top": "rgb(227,49,44)",
      "bot": "rgb(100,22,19)",
      "txt": "#fff"
    }
  },
  {
    "c": "Pouso Alegre",
    "slug": "pouso-alegre",
    "sourceName": "Pouso Alegre",
    "group": "A13",
    "rep": -1,
    "logo": "assets/database/crests/serie-d-2026/pouso-alegre.png",
    "sourceLogo": "https://assets.candangol.com.br/cdn-cgi/image/width=128,quality=78,format=auto/teams/pouso-alegre/pouso-alegre.webp",
    "palette": {
      "top": "rgb(167,28,37)",
      "bot": "rgb(74,13,16)",
      "txt": "#fff"
    }
  },
  {
    "c": "Primavera-MT",
    "slug": "primavera-mt",
    "sourceName": "Primavera",
    "group": "A3",
    "rep": -1,
    "logo": "assets/database/crests/serie-d-2026/primavera-mt.png",
    "sourceLogo": "https://assets.candangol.com.br/cdn-cgi/image/width=128,quality=78,format=auto/teams/primavera-mt/primavera-mt.webp",
    "palette": {
      "top": "rgb(100,52,154)",
      "bot": "rgb(44,23,68)",
      "txt": "#fff"
    }
  },
  {
    "c": "Real Noroeste",
    "slug": "real-noroeste",
    "sourceName": "Real Noroeste",
    "group": "A12",
    "rep": -1,
    "logo": "assets/database/crests/serie-d-2026/real-noroeste.png",
    "sourceLogo": "https://assets.candangol.com.br/cdn-cgi/image/width=128,quality=78,format=auto/teams/real-noroeste/real-noroeste.webp",
    "palette": {
      "top": "rgb(220,39,30)",
      "bot": "rgb(97,17,13)",
      "txt": "#fff"
    }
  },
  {
    "c": "Retrô",
    "slug": "retro",
    "sourceName": "Retrô",
    "group": "A9",
    "rep": 0,
    "logo": "assets/database/crests/serie-d-2026/retro.png",
    "sourceLogo": "https://assets.candangol.com.br/cdn-cgi/image/width=128,quality=78,format=auto/teams/retro/retro.webp",
    "palette": {
      "top": "rgb(38,37,79)",
      "bot": "rgb(17,16,35)",
      "txt": "#fff"
    }
  },
  {
    "c": "Rio Branco-ES",
    "slug": "rio-branco-es",
    "sourceName": "Rio Branco",
    "group": "A12",
    "rep": -1,
    "logo": "assets/database/crests/serie-d-2026/rio-branco-es.png",
    "sourceLogo": "https://assets.candangol.com.br/cdn-cgi/image/width=128,quality=78,format=auto/teams/rio-branco-es/rio-branco-es.webp",
    "palette": {
      "top": "rgb(43,43,43)",
      "bot": "rgb(19,19,19)",
      "txt": "#fff"
    }
  },
  {
    "c": "Sampaio Corrêa-MA",
    "slug": "sampaio-correa",
    "sourceName": "Sampaio Corrêa",
    "group": "A6",
    "rep": 0,
    "logo": "assets/database/crests/serie-d-2026/sampaio-correa.png",
    "sourceLogo": "https://assets.candangol.com.br/cdn-cgi/image/width=128,quality=78,format=auto/teams/sampaio-correa/sampaio-correa.webp",
    "palette": {
      "top": "rgb(230,186,15)",
      "bot": "rgb(102,82,7)",
      "txt": "#fff"
    }
  },
  {
    "c": "Sampaio Corrêa-RJ",
    "slug": "sampaio-correa-rj",
    "sourceName": "Sampaio Corrêa-RJ",
    "group": "A14",
    "rep": -1,
    "logo": "assets/database/crests/serie-d-2026/sampaio-correa-rj.png",
    "sourceLogo": "https://assets.candangol.com.br/cdn-cgi/image/width=128,quality=78,format=auto/teams/sampaio-correa-rj/sampaio-correa-rj.webp",
    "palette": {
      "top": "rgb(220,176,30)",
      "bot": "rgb(97,78,13)",
      "txt": "#fff"
    }
  },
  {
    "c": "Santa Catarina",
    "slug": "santa-catarina",
    "sourceName": "Santa Catarina",
    "group": "A15",
    "rep": -1,
    "logo": "assets/database/crests/serie-d-2026/santa-catarina.png",
    "sourceLogo": "https://assets.candangol.com.br/cdn-cgi/image/width=128,quality=78,format=auto/teams/santa-catarina/santa-catarina.webp",
    "palette": {
      "top": "rgb(211,99,9)",
      "bot": "rgb(93,44,4)",
      "txt": "#fff"
    }
  },
  {
    "c": "São José-RS",
    "slug": "sao-jose-rs",
    "sourceName": "São José-RS",
    "group": "A16",
    "rep": -1,
    "logo": "assets/database/crests/serie-d-2026/sao-jose-rs.png",
    "sourceLogo": "https://assets.candangol.com.br/cdn-cgi/image/width=128,quality=78,format=auto/teams/sao-jose-rs/sao-jose-rs.webp",
    "palette": {
      "top": "rgb(41,45,93)",
      "bot": "rgb(18,20,41)",
      "txt": "#fff"
    }
  },
  {
    "c": "São Joseense",
    "slug": "sao-joseense",
    "sourceName": "São Joseense",
    "group": "A16",
    "rep": -1,
    "logo": "assets/database/crests/serie-d-2026/sao-joseense.png",
    "sourceLogo": "https://assets.candangol.com.br/cdn-cgi/image/width=128,quality=78,format=auto/teams/sao-joseense/sao-joseense.webp",
    "palette": {
      "top": "rgb(44,80,152)",
      "bot": "rgb(19,35,67)",
      "txt": "#fff"
    }
  },
  {
    "c": "São Luiz",
    "slug": "sao-luiz-ijui",
    "sourceName": "São Luiz",
    "group": "A15",
    "rep": -1,
    "logo": "assets/database/crests/serie-d-2026/sao-luiz-ijui.png",
    "sourceLogo": "https://assets.candangol.com.br/cdn-cgi/image/width=128,quality=78,format=auto/teams/sao-luiz-ijui/sao-luiz-ijui.webp",
    "palette": {
      "top": "rgb(228,57,63)",
      "bot": "rgb(101,25,28)",
      "txt": "#fff"
    }
  },
  {
    "c": "São Raimundo-RR",
    "slug": "sao-raimundo-rr",
    "sourceName": "São Raimundo",
    "group": "A1",
    "rep": -1,
    "logo": "assets/database/crests/serie-d-2026/sao-raimundo-rr.png",
    "sourceLogo": "https://assets.candangol.com.br/cdn-cgi/image/width=128,quality=78,format=auto/teams/sao-raimundo-rr/sao-raimundo-rr.webp",
    "palette": {
      "top": "rgb(24,76,168)",
      "bot": "rgb(10,34,74)",
      "txt": "#fff"
    }
  },
  {
    "c": "Sergipe",
    "slug": "sergipe",
    "sourceName": "Sergipe",
    "group": "A9",
    "rep": -1,
    "logo": "assets/database/crests/serie-d-2026/sergipe.png",
    "sourceLogo": "https://assets.candangol.com.br/cdn-cgi/image/width=128,quality=78,format=auto/teams/sergipe/sergipe.webp",
    "palette": {
      "top": "rgb(240,39,39)",
      "bot": "rgb(106,17,17)",
      "txt": "#fff"
    }
  },
  {
    "c": "Serra Branca",
    "slug": "serra-branca",
    "sourceName": "Serra Branca",
    "group": "A9",
    "rep": -1,
    "logo": "assets/database/crests/serie-d-2026/serra-branca.png",
    "sourceLogo": "https://assets.candangol.com.br/cdn-cgi/image/width=128,quality=78,format=auto/teams/serra-branca/serra-branca.webp",
    "palette": {
      "top": "rgb(21,66,113)",
      "bot": "rgb(9,29,50)",
      "txt": "#fff"
    }
  },
  {
    "c": "Sousa",
    "slug": "sousa",
    "sourceName": "Sousa",
    "group": "A8",
    "rep": -1,
    "logo": "assets/database/crests/serie-d-2026/sousa.png",
    "sourceLogo": "https://assets.candangol.com.br/cdn-cgi/image/width=128,quality=78,format=auto/teams/sousa/sousa.webp",
    "palette": {
      "top": "rgb(15,102,43)",
      "bot": "rgb(7,45,19)",
      "txt": "#fff"
    }
  },
  {
    "c": "Tirol",
    "slug": "tirol",
    "sourceName": "Tirol",
    "group": "A7",
    "rep": -1,
    "logo": "assets/database/crests/serie-d-2026/tirol.png",
    "sourceLogo": "https://assets.candangol.com.br/cdn-cgi/image/width=128,quality=78,format=auto/teams/tirol/tirol.webp",
    "palette": {
      "top": "rgb(15,51,134)",
      "bot": "rgb(6,22,59)",
      "txt": "#fff"
    }
  },
  {
    "c": "Tocantinópolis",
    "slug": "tocantinopolis",
    "sourceName": "Tocantinópolis",
    "group": "A5",
    "rep": -1,
    "logo": "assets/database/crests/serie-d-2026/tocantinopolis.png",
    "sourceLogo": "https://assets.candangol.com.br/cdn-cgi/image/width=128,quality=78,format=auto/teams/tocantinopolis/tocantinopolis.webp",
    "palette": {
      "top": "rgb(35,145,79)",
      "bot": "rgb(15,64,35)",
      "txt": "#fff"
    }
  },
  {
    "c": "Tombense",
    "slug": "tombense",
    "sourceName": "Tombense",
    "group": "A12",
    "rep": 0,
    "logo": "assets/database/crests/serie-d-2026/tombense.png",
    "sourceLogo": "https://assets.candangol.com.br/cdn-cgi/image/width=128,quality=78,format=auto/teams/tombense/tombense.webp",
    "palette": {
      "top": "rgb(223,56,63)",
      "bot": "rgb(98,25,28)",
      "txt": "#fff"
    }
  },
  {
    "c": "Trem",
    "slug": "trem",
    "sourceName": "Trem",
    "group": "A5",
    "rep": -1,
    "logo": "assets/database/crests/serie-d-2026/trem.png",
    "sourceLogo": "https://assets.candangol.com.br/cdn-cgi/image/width=128,quality=78,format=auto/teams/trem/trem.webp",
    "palette": {
      "top": "rgb(200,14,12)",
      "bot": "rgb(88,6,5)",
      "txt": "#fff"
    }
  },
  {
    "c": "Treze",
    "slug": "treze",
    "sourceName": "Treze",
    "group": "A9",
    "rep": -1,
    "logo": "assets/database/crests/serie-d-2026/treze.png",
    "sourceLogo": "https://assets.candangol.com.br/cdn-cgi/image/width=128,quality=78,format=auto/teams/treze/treze.webp",
    "palette": {
      "top": "rgb(133,133,133)",
      "bot": "rgb(59,59,59)",
      "txt": "#fff"
    }
  },
  {
    "c": "Tuna Luso",
    "slug": "tuna-luso",
    "sourceName": "Tuna Luso",
    "group": "A5",
    "rep": -1,
    "logo": "assets/database/crests/serie-d-2026/tuna-luso.png",
    "sourceLogo": "https://assets.candangol.com.br/cdn-cgi/image/width=128,quality=78,format=auto/teams/tuna-luso/tuna-luso.webp",
    "palette": {
      "top": "rgb(25,147,76)",
      "bot": "rgb(11,65,34)",
      "txt": "#fff"
    }
  },
  {
    "c": "Uberlândia",
    "slug": "uberlandia",
    "sourceName": "Uberlândia",
    "group": "A11",
    "rep": -1,
    "logo": "assets/database/crests/serie-d-2026/uberlandia.png",
    "sourceLogo": "https://assets.candangol.com.br/cdn-cgi/image/width=128,quality=78,format=auto/teams/uberlandia/uberlandia.webp",
    "palette": {
      "top": "rgb(23,134,48)",
      "bot": "rgb(10,59,21)",
      "txt": "#fff"
    }
  },
  {
    "c": "União Rondonópolis",
    "slug": "uniao-rondonopolis",
    "sourceName": "União Rondonópolis",
    "group": "A4",
    "rep": -1,
    "logo": "assets/database/crests/serie-d-2026/uniao-rondonopolis.png",
    "sourceLogo": "https://assets.candangol.com.br/cdn-cgi/image/width=128,quality=78,format=auto/teams/uniao-rondonopolis/uniao-rondonopolis.webp",
    "palette": {
      "top": "rgb(211,40,46)",
      "bot": "rgb(93,18,20)",
      "txt": "#fff"
    }
  },
  {
    "c": "Velo Clube",
    "slug": "velo-clube",
    "sourceName": "Velo Clube",
    "group": "A14",
    "rep": -1,
    "logo": "assets/database/crests/serie-d-2026/velo-clube.png",
    "sourceLogo": "https://assets.candangol.com.br/cdn-cgi/image/width=128,quality=78,format=auto/teams/velo-clube/velo-clube.webp",
    "palette": {
      "top": "rgb(17,166,89)",
      "bot": "rgb(8,73,39)",
      "txt": "#fff"
    }
  },
  {
    "c": "Vitória-ES",
    "slug": "vitoria-es",
    "sourceName": "Vitória",
    "group": "A12",
    "rep": -1,
    "logo": "assets/database/crests/serie-d-2026/vitoria-es.png",
    "sourceLogo": "https://assets.candangol.com.br/cdn-cgi/image/width=128,quality=78,format=auto/teams/vitoria-es/vitoria-es.webp",
    "palette": {
      "top": "rgb(38,55,162)",
      "bot": "rgb(17,24,72)",
      "txt": "#fff"
    }
  },
  {
    "c": "XV de Piracicaba",
    "slug": "xv-de-piracicaba",
    "sourceName": "XV de Piracicaba",
    "group": "A14",
    "rep": -1,
    "logo": "assets/database/crests/serie-d-2026/xv-de-piracicaba.png",
    "sourceLogo": "https://assets.candangol.com.br/cdn-cgi/image/width=128,quality=78,format=auto/teams/xv-de-piracicaba/xv-de-piracicaba.webp",
    "palette": {
      "top": "rgb(133,133,133)",
      "bot": "rgb(59,59,59)",
      "txt": "#fff"
    }
  }
];
  // Os 96 participantes oficiais ficam na Série D; os convidados começam sem divisão nacional.
  // Feira-FC usa o verde solicitado pelo autor, ausente no escudo.
  const guestTeams=[
  {
    "c": "Futobeso-FC",
    "rep": -1,
    "logo": "assets/database/crests/serie-d-2026/futobeso-fc.png",
    "palette": {
      "top": "rgb(10,45,144)",
      "bot": "rgb(5,20,64)",
      "txt": "#fff"
    }
  },
  {
    "c": "Feira-FC",
    "rep": -1,
    "logo": "assets/database/crests/serie-d-2026/feira-fc.png",
    "palette": {
      "top": "#148347",
      "bot": "#073a22",
      "txt": "#fff"
    }
  },
  {
    "c": "Íbis",
    "rep": -1,
    "logo": "assets/database/crests/serie-d-2026/ibis.png",
    "palette": {"top":"rgb(220,29,37)","bot":"rgb(92,12,16)","txt":"#fff"}
  },
  {
    "c": "PQP",
    "rep": -1,
    "logo": "assets/database/crests/serie-d-2026/pqp.png",
    "palette": {"top":"rgb(8,31,74)","bot":"rgb(3,12,32)","txt":"#fff"}
  },
  {
    "c": "FC Gravidez",
    "rep": -1,
    "logo": "assets/database/crests/serie-d-2026/fc-gravidez.png",
    "palette": {"top":"rgb(53,25,87)","bot":"rgb(23,10,42)","txt":"#fff"}
  }
];
  global.COPERO_SERIE_D={...metadata,teams,guestTeams};
  global.COPERO_TIMES.ligas.push({id:'brasileirao-serie-d',nome:'Brasileirão Série D',code:'BRA4',pais:'BRA',conf:'CONMEBOL',tier:4,copa:null,times:teams.length});
  global.COPERO_LIGAS.BRA4=['Brasileirão Série D','Série D','Brasil'];
  global.COPERO_PESO_LIGA.BRA4=30;
  global.COPERO_CONF_LIGA.BRA4='CONMEBOL';
  global.COPERO_FIFA_LIGA.BRA4='BRA';
  // BRA0 é uma categoria de cadastro: não participa da hierarquia de ligas.
  global.COPERO_LIGAS.BRA0=['Sem divisão','Sem divisão','Brasil'];
  global.COPERO_PESO_LIGA.BRA0=20;
  global.COPERO_CONF_LIGA.BRA0='CONMEBOL';
  global.COPERO_FIFA_LIGA.BRA0='BRA';
  for (const team of [...teams,...guestTeams]) {
    const semDivisao=guestTeams.includes(team),league=semDivisao?'BRA0':'BRA4';
    global.COPERO_CLUBES.push({c:team.c,l:league,k:'',tier:'C',div:semDivisao?0:4,rep:team.rep,repDom:0,repCont:0,baseOvr:team.rep===0?58:52,isSA:true,isEU:false,logo:team.logo,fifa:'BRA'});
    global.COPERO_LOGOS[league+'|'+team.c]=team.logo;
  }
})(window);
