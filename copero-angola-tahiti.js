/* Cadastro exclusivo do Copero; reputações são balanceamento do jogo, não notas das fontes. */
(function (global) {
  'use strict';
  // Calculadas com corDoEscudo (index.html); recalcular ao substituir os escudos.
  const palettes={
  "petro": {
    "top": "rgb(186,160,42)",
    "bot": "rgb(98,84,22)",
    "txt": "#fff"
  },
  "dago": {
    "top": "rgb(169,35,26)",
    "bot": "rgb(75,15,11)",
    "txt": "#fff"
  },
  "sagrada": {
    "top": "rgb(63,162,114)",
    "bot": "rgb(28,72,50)",
    "txt": "#fff"
  },
  "wiliete": {
    "top": "rgb(199,189,15)",
    "bot": "rgb(105,99,8)",
    "txt": "#111"
  },
  "interclube": {
    "top": "rgb(3,53,171)",
    "bot": "rgb(1,24,75)",
    "txt": "#fff"
  },
  "desphuila": {
    "top": "rgb(153,135,35)",
    "bot": "rgb(68,60,15)",
    "txt": "#fff"
  },
  "kabuscorp": {
    "top": "rgb(220,60,67)",
    "bot": "rgb(97,27,29)",
    "txt": "#fff"
  },
  "bravos": {
    "top": "rgb(46,80,57)",
    "bot": "rgb(20,35,25)",
    "txt": "#fff"
  },
  "lundasul": {
    "top": "rgb(65,184,229)",
    "bot": "rgb(29,81,101)",
    "txt": "#fff"
  },
  "libolo": {
    "top": "rgb(40,98,172)",
    "bot": "rgb(18,43,76)",
    "txt": "#fff"
  },
  "lobito": {
    "top": "rgb(167,137,10)",
    "bot": "rgb(74,61,4)",
    "txt": "#fff"
  },
  "saosalvador": {
    "top": "rgb(226,5,21)",
    "bot": "rgb(100,2,9)",
    "txt": "#fff"
  },
  "primeiromaio": {
    "top": "rgb(157,25,10)",
    "bot": "rgb(69,11,4)",
    "txt": "#fff"
  },
  "fcluanda": {
    "top": "rgb(16,58,107)",
    "bot": "rgb(7,26,47)",
    "txt": "#fff"
  },
  "redonda": {
    "top": "rgb(233,54,87)",
    "bot": "rgb(103,24,39)",
    "txt": "#fff"
  },
  "guelson": {
    "top": "rgb(177,73,43)",
    "bot": "rgb(78,32,19)",
    "txt": "#fff"
  },
  "pirae": {
    "top": "rgb(173,28,39)",
    "bot": "rgb(76,12,17)",
    "txt": "#fff"
  },
  "tefana": {
    "top": "rgb(191,188,41)",
    "bot": "rgb(84,83,18)",
    "txt": "#fff"
  },
  "venus": {
    "top": "rgb(57,49,140)",
    "bot": "rgb(25,21,62)",
    "txt": "#fff"
  },
  "dragon": {
    "top": "rgb(70,88,161)",
    "bot": "rgb(31,39,71)",
    "txt": "#fff"
  },
  "punaruu": {
    "top": "rgb(216,131,26)",
    "bot": "rgb(95,58,12)",
    "txt": "#fff"
  },
  "central": {
    "top": "rgb(164,8,42)",
    "bot": "rgb(72,4,19)",
    "txt": "#fff"
  },
  "pueu-clean": {
    "top": "rgb(1,114,179)",
    "bot": "rgb(0,50,79)",
    "txt": "#fff"
  },
  "taiarapu": {
    "top": "rgb(19,187,21)",
    "bot": "rgb(8,83,9)",
    "txt": "#fff"
  },
  "mira-clean": {
    "top": "rgb(21,148,211)",
    "bot": "rgb(9,66,93)",
    "txt": "#fff"
  },
  "arue-clean": {
    "top": "rgb(133,133,133)",
    "bot": "rgb(59,59,59)",
    "txt": "#fff"
  },
  "excelsior-clean": {
    "top": "rgb(12,34,151)",
    "bot": "rgb(5,15,67)",
    "txt": "#fff"
  },
  "manu-ura-clean": {
    "top": "rgb(133,133,133)",
    "bot": "rgb(59,59,59)",
    "txt": "#fff"
  },
  "mataiea-clean": {
    "top": "rgb(171,13,23)",
    "bot": "rgb(76,6,10)",
    "txt": "#fff"
  },
  "jeunes-tahitiens-clean": {
    "top": "rgb(49,76,155)",
    "bot": "rgb(22,34,68)",
    "txt": "#fff"
  }
};
  const leagues=[
    {
      id:'girabola',code:'ANG1',nome:'Girabola',country:'Angola',pais:'ANG',conf:'CAF',weight:45,
      season:'2025/26',source:'https://www.rsssf.org/tablesa/ango2026.html',
      crestSource:'https://www.ligaunitelgirabola.com/teams',
      // [nome, escudo, reputação internacional, doméstica, continental]
      teams:[
        ['Petro de Luanda','petro',1,4,2],
        ['1º de Agosto','dago',0,3,1],
        ['Sagrada Esperança','sagrada',0,2,1],
        ['Wiliete SC','wiliete',0,2,0],
        ['Interclube','interclube',0,1,0],
        ['Desportivo da Huíla','desphuila',-1,1,0],
        ['Kabuscorp','kabuscorp',-1,1,0],
        ['Bravos do Maquis','bravos',-1,1,0],
        ['Desportivo da Lunda-Sul','lundasul',-1,0,0],
        ['Recreativo do Libolo','libolo',-1,1,0],
        ['Académica do Lobito','lobito',-1,0,0],
        ['São Salvador','saosalvador',-1,0,0],
        ['1º de Maio de Benguela','primeiromaio',-1,0,0],
        ['Luanda City','fcluanda',-1,0,0],
        ['Redonda FC','redonda',-1,0,0],
        ['RSD Guelson FC','guelson',-1,0,0]
      ]
    },
    {
      id:'tahiti-ligue-1',code:'TAH1',nome:'Ligue 1 do Tahiti',country:'Tahiti',pais:'TAH',conf:'OFC',weight:25,
      season:'2026/27',source:'https://tps.ftf.pf/2026-2027/championnat_seniors_hommes_de_tahiti_techni-bois',
      crestSource:'https://www.ogol.com.br/competicao/liga-taiti',
      crestFallback:'AS Mira: https://www.ftf.pf/clubs/clubs-de-moorea/',
      // As equipes 2 disputam a mesma competição que as principais.
      teams:[
        ['AS Pirae','pirae',-1,4,2],
        ['AS Tefana','tefana',-1,4,1],
        ['AS Vénus','venus',-1,3,1],
        ['AS Dragon','dragon',-1,2,1],
        ['AS Tamarii Punaruu','punaruu',-1,1,0],
        ['AS Central Sport','central',-1,1,0],
        ['AS Pueu','pueu-clean',-1,0,0],
        ['AS Taiarapu FC','taiarapu',-1,0,0],
        ['AS Jeunes Tahitiens','jeunes-tahitiens-clean',-1,0,0],
        ['AS Arue','arue-clean',-1,0,0],
        ['AS Excelsior','excelsior-clean',-1,0,0],
        ['AS Mataiea','mataiea-clean',-1,0,0],
        ['AS Manu Ura','manu-ura-clean',-1,0,0],
        ['AS Tefana B','tefana',-1,0,0],
        ['AS Central Sport B','central',-1,0,0],
        ['AS Tamarii Punaruu B','punaruu',-1,0,0]
      ],
      // Mantido para as carreiras já iniciadas em 2025/26, sem contá-lo entre os 16 participantes.
      legacyTeams:[['AS Mira','mira-clean',-1,1,0]]
    }
  ];
  global.COPERO_ANGOLA_TAHITI={leagues};
  for (const league of leagues) {
    const {id,code,nome,pais,conf,teams}=league;
    global.COPERO_TIMES.ligas.push({id,code,nome,pais,conf,tier:1,copa:null,times:teams.length});
    global.COPERO_LIGAS[code]=[nome,nome,league.country];
    global.COPERO_PESO_LIGA[code]=league.weight;
    global.COPERO_CONF_LIGA[code]=conf;
    global.COPERO_FIFA_LIGA[code]=pais;
    const legacyTeams=league.legacyTeams||[];
    for (const team of [...teams,...legacyTeams]) {
      const [c,slug,rep,repDom,repCont]=team;
      const logo='assets/database/crests/angola-tahiti/'+slug+'.png';
      global.COPERO_CLUBES.push({c,l:code,k:'',tier:rep===1?'B':'C',div:1,rep,repDom,repCont,baseOvr:rep===1?68:rep===0?58:52,isSA:false,isEU:false,logo,fifa:pais,palette:palettes[slug],legacy:legacyTeams.includes(team)});
      global.COPERO_LOGOS[code+'|'+c]=logo;
    }
  }
})(window);
