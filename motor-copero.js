/* =====================================================================
   MOTOR COPERO — porte fiel do Simulador de Carreira do copero.com.ar
   ---------------------------------------------------------------------
   Arquivo:  motor-copero.js
   Alvo:     navegador (window.MotorCopero) e Node (module.exports)
   Base:     reverse do bundle live CareerSimulatorPage-*.js (v2026-10)
   Puro (sem DOM). Dados + regras. A UI do index3.html consome via adapter.
   ===================================================================== */
(function (global) {
  'use strict';

  /* ============================================================
     1 · DADOS  (o "sistema de dados" do Copero)
     RNG determinístico: hash FNV-1a -> xorshift32.
     Mesma seed + mesmo passo => mesma carreira, sempre.
     ============================================================ */
  function hashSeed(str) {
    let o = 2166136261;
    for (let i = 0; i < str.length; i++) {
      o ^= str.charCodeAt(i);
      o = Math.imul(o, 16777619);
    }
    return (o >>> 0) || 1;
  }
  function mkRng(seed) { return { seed: seed, state: hashSeed(String(seed)) }; }
  function next(rng) {
    let o = rng.state;
    o ^= o << 13; o ^= o >>> 17; o ^= o << 5;
    const a = (o >>> 0) || 1;
    return { rng: { seed: rng.seed, state: a }, value: a / 4294967296 };
  }
  function _num(rng, min, max) {
    const r = next(rng);
    return { rng: r.rng, value: min + r.value * (max - min) };
  }
  function _int(rng, min, max) {
    const r = _num(rng, 0, 1);
    return { rng: r.rng, value: Math.floor(r.value * (max - min + 1)) + min };
  }
  const RNG = {
    make: mkRng,
    next: next,
    num: _num,
    int: _int,
    chance(rng, p) {
      const q = Math.max(0, Math.min(1, p));
      const r = next(rng);
      return { rng: r.rng, success: r.value < q };
    },
    pick(rng, arr) {
      if (!arr.length) throw new Error('pick: lista vazia');
      const r = _int(rng, 0, arr.length - 1);
      return { rng: r.rng, item: arr[r.value] };
    },
    weighted(rng, list) {           // list: [{item, weight}]
      const total = list.reduce((a, x) => a + Math.max(0, x.weight), 0);
      if (!list.length || total <= 0) throw new Error('weighted: pesos zero');
      const r = _num(rng, 0, total);
      let acc = 0;
      for (const x of list) {
        acc += Math.max(0, x.weight);
        if (r.value <= acc) return { rng: r.rng, item: x.item };
      }
      return { rng: r.rng, item: list[list.length - 1].item };
    },
    // deriva um RNG novo a partir de "seed:contexto"
    fork(rng, ctx) { return mkRng(String(rng.seed) + ':' + ctx); }
  };

  /* ============================================================
     2 · TABELAS DO COPERO
     ============================================================ */
  const CLAMP = (v, a, b) => Math.max(a, Math.min(b, v));

  // Modos e duração do período (temporadas por bloco)
  const MODES = {
    long:    { periodLengthSeasons: 1, personalEventCount: [6, 7], substituteBeforeNonRenewal: 2, lowRotationBeforeNonRenewal: 3 },
    normal:  { periodLengthSeasons: 2, personalEventCount: [3, 4], substituteBeforeNonRenewal: 1, lowRotationBeforeNonRenewal: 2 },
    express: { periodLengthSeasons: 3, personalEventCount: [2, 3], substituteBeforeNonRenewal: 1, lowRotationBeforeNonRenewal: 2 }
  };
  const RETIRE_AGE = 40;
  const REP_LEVELS = 5;         // 0..5 (com -1 tratado à parte)

  // OVR de referência do clube por reputação internacional (-1 = clube fraco)
  const REP_OVR = { '-1': 52, 0: 58, 1: 68, 2: 75, 3: 80, 4: 84, 5: 88 };
  const baseOvrOf = (rep) => REP_OVR[rep] ?? REP_OVR[0];

  // Tabela de valor de mercado (€) por OVR + fator de idade
  const VALUE_TAB = [[50, 1e5], [55, 25e4], [60, 5e5], [65, 12e5], [70, 3e6], [75, 5e6], [80, 15e6], [85, 5e7], [90, 1e8], [95, 15e7], [99, 25e7]];
  const ageValueFactor = (age) => age <= 18 ? 1.5 : age <= 22 ? 1.2 : age <= 26 ? 1 : age <= 30 ? 0.9 : age <= 32 ? 0.8 : age <= 34 ? 0.6 : 0.2;
  function roundValue(v) {
    if (v >= 1e7) return Math.round(v / 1e6) * 1e6;
    if (v >= 1e6) return Math.round(v / 1e5) * 1e5;
    return Math.round(v / 1e4) * 1e4;
  }
  function marketValue(rng, ovr, age) {
    const o = CLAMP(ovr, 50, 99);
    let i = -1;
    for (let k = 0; k < VALUE_TAB.length; k++) if (VALUE_TAB[k][0] <= o) i = k;
    const lo = VALUE_TAB[Math.max(0, i)];
    const hi = VALUE_TAB.find(x => x[0] >= o) ?? VALUE_TAB[VALUE_TAB.length - 1];
    const [a, va] = lo, [b, vb] = hi;
    const m = b === a ? 0 : (o - a) / (b - a);
    const base = va + (vb - va) * m;
    const jitter = _num(rng, 0.95, 1.05);
    return { rng: jitter.rng, value: roundValue(base * ageValueFactor(age) * jitter.value) };
  }

  // Progressão de OVR: delta total do ciclo de 2 anos por perfil
  const DEV = {
    early:  { 18: [7, 16], 20: [6, 16], 22: [4, 10], 24: [0, 7], 26: [-2, 1], 28: [-2, -1], 30: [-2, 0], 32: [-4, 0], 34: [-6, -1], 36: [-8, -2], 38: [-10, -3] },
    normal: { 18: [4, 14], 20: [3, 14], 22: [2, 10], 24: [1, 8], 26: [0, 3], 28: [-1, 0], 30: [-1, 0], 32: [-3, 0], 34: [-5, -1], 36: [-7, -2], 38: [-10, -3] },
    late:   { 18: [2, 12], 20: [1, 12], 22: [1, 9], 24: [2, 9], 26: [1, 5], 28: [0, 1], 30: [0, 1], 32: [-2, 0], 34: [-5, -1], 36: [-7, -2], 38: [-10, -3] }
  };
  // Goleiro tem tabela própria (Copero)
  const DEV_GK = { 18: [2, 10], 20: [2, 10], 22: [2, 9], 24: [2, 8], 26: [1, 7], 28: [1, 5], 30: [0, 0], 32: [-1, 0], 34: [-2, 0], 36: [-4, -1], 38: [-6, -2] };
  const rollProfile = (r) => r < 0.1 ? 'early' : r < 0.2 ? 'late' : 'normal';

  // Reputação-alvo do jogador pelo OVR (usado em propostas)
  const offerReputation = (ovr) =>
    ovr >= 87 ? 5 : ovr >= 83 ? 4 : ovr >= 78 ? 3 : ovr >= 73 ? 2 : ovr >= 65 ? 1 : ovr >= 55 ? 0 : -1;

  // Lesões (mesma tabela do Copero)
  const INJURIES = [
    { type: 'hamstring', weight: 24, ovr: -3 }, { type: 'meniscus', weight: 18, ovr: -2 },
    { type: 'acl', weight: 14, ovr: -5 }, { type: 'tibia_fibula', weight: 8, ovr: -8 },
    { type: 'achilles', weight: 4, ovr: -10 }, { type: 'ankle_sprain', weight: 14, ovr: -1 },
    { type: 'calf_tear', weight: 8, ovr: -2 }, { type: 'metatarsal_fracture', weight: 5, ovr: -4 },
    { type: 'shoulder_dislocation', weight: 3, ovr: -4 }, { type: 'disc_hernia', weight: 2, ovr: -5 }
  ];
  const injuryOvr = (type) => (INJURIES.find(x => x.type === type) || { ovr: -3 }).ovr;
  const INJURY_CHANCE = 0.02;
  const MAX_INJURIES_PER_CAREER = 2;

  /* Papéis e setores ------------------------------------------------ */
  const ROLE_GROUPS = {
    attacker: ['LW', 'ST', 'RW'],
    creator:  ['LM', 'CAM', 'RM'],
    support:  ['LB', 'CM', 'RB'],
    defensive:['CDM', 'CB'],
    goalkeeper:['GK']
  };
  // Mapas PT (posições do index3) -> posição Copero -> setor
  const POS_COPERO = { CA: 'ST', SA: 'ST', PD: 'RW', PE: 'LW', MEI: 'CAM', MC: 'CM', VOL: 'CDM', LD: 'RB', LE: 'LB', ZAG: 'CB', GOL: 'GK' };
  const POS_GROUPS = { CA: 'attacker', SA: 'attacker', PD: 'attacker', PE: 'attacker', MEI: 'creator', MC: 'support', VOL: 'defensive', LD: 'support', LE: 'support', ZAG: 'defensive', GOL: 'goalkeeper' };
  const groupOf = (pos) => POS_GROUPS[pos] || 'support';
  const isGk = (pos) => pos === 'GOL' || pos === 'GK';

  // Faixa de jogos por papel
  function appearanceRange(role, gk) {
    if (gk) return role === 'starter' ? [42, 50] : role === 'third_keeper' ? [0, 4] : [2, 12];
    return role === 'starter' ? [40, 50] : role === 'high_rotation' ? [25, 39] : role === 'low_rotation' ? [15, 24] : [5, 14];
  }
  // Papel pelo OVR contra a força do clube
  function roleFromDiff(diff, gk) {
    if (gk) return diff >= 0 ? 'starter' : diff >= -6 ? 'substitute' : 'third_keeper';
    return diff >= 0 ? 'starter' : diff >= -4 ? 'high_rotation' : diff >= -8 ? 'low_rotation' : 'substitute';
  }
  const ROLE_ORDER = ['substitute', 'low_rotation', 'high_rotation', 'starter'];
  const ROLE_ORDER_GK = ['third_keeper', 'substitute', 'starter'];
  function shiftRole(role, gk, shift) {
    if (!shift) return role;
    const arr = gk ? ROLE_ORDER_GK : ROLE_ORDER;
    const i = arr.indexOf(role);
    return arr[CLAMP(i + shift, 0, arr.length - 1)] ?? role;
  }
  const isLowRotation = (r) => r === 'low_rotation';
  const isBench = (r) => r === 'substitute' || r === 'third_keeper';

  // Multiplicador de presença por reputação do clube
  const appearanceMult = (club) =>
    club.domesticReputation === 0 ? 0.7 : club.domesticReputation === 1 ? 0.8 : club.continentalReputation === 0 ? 0.9 : 1;

  // Banda por diferença de OVR
  const bandOf = (d) => d >= 10 ? 0 : d >= 6 ? 1 : d >= 3 ? 2 : d >= -2 ? 3 : d >= -5 ? 4 : d >= -9 ? 5 : 6;
  const GOAL_RATE = {
    attacker: [1.1, .85, .65, .5, .3, .15, .05],
    creator:  [.85, .6, .45, .3, .2, .1, .05],
    support:  [.15, .1, .08, .05, .02, 0, 0],
    defensive:[.1, .08, .06, .04, .02, 0, 0],
    goalkeeper:[0, 0, 0, 0, 0, 0, 0]
  };
  const ASSIST_RATE = {
    attacker: [.4, .3, .2, .15, .1, .08, .05],
    creator:  [.6, .45, .35, .25, .15, .08, .05],
    support:  [.35, .25, .18, .12, .07, .03, .02],
    defensive:[.1, .07, .05, .03, .01, 0, 0],
    goalkeeper:[0, 0, 0, 0, 0, 0, 0]
  };
  const teamStrengthMult = (rep) => [.55, .75, .95, 1, 1.1, 1.2][CLAMP(rep, 0, 5)];
  function finishingMult(ovr) {
    const o = CLAMP(ovr, 40, 99);
    if (o <= 65) return .6;
    if (o <= 80) return .6 + (o - 65) / 15 * .25;
    if (o <= 85) return .85 + (o - 80) / 5 * .15;
    if (o <= 95) return 1 + (o - 85) / 10 * .1;
    return 1.1;
  }
  const gkConcededMult = (d) => d >= 10 ? .5 : d >= 6 ? .75 : d >= 3 ? .9 : d >= -2 ? 1 : d >= -5 ? 1.1 : d >= -9 ? 1.2 : 1.35;

  /* Probabilidades de título ---------------------------------------- */
  const PROB = {
    league: [0, .01, .05, .25, .45, .7],
    cup:    [.01, .04, .1, .25, .35, .4],
    continentalPrimary: [0, 1e-5, .03, .15, .2, .3],
    continentalSecondary: [0, .04, .12, .02, 0, 0],   // usado só onde há secundária (UEFA/CONMEBOL)
    clubWorldCupByConfederation: {
      UEFA: [0, 0, .005, .05, .1, .15],
      CONMEBOL: [0, 0, 0, .002, .005, 0],
      CONCACAF: [0, 0, 0, 1e-4, 0, 0]
    }
  };
  const CONFEDS_WITH_SECONDARY = new Set(['UEFA', 'CONMEBOL', 'CONCACAF']);
  const clubWorldCupYear = (age) => age >= 18 && (age - 18) % 4 === 0;

  // Reputação efetiva do clube sobe conforme o OVR do jogador (regra Copero)
  function effectiveRep(ovr, club) {
    const rep = CLAMP(club.internationalReputation, -1, 5);
    let dDom = 0, dCont = 0;
    if (ovr >= 90) {
      if (rep === 3) { dDom = 1; dCont = 1; }
      else if (rep === 2) { dDom = 2; dCont = 1; }
      else if (rep <= 1) { dDom = 2; dCont = 2; }
    } else if (ovr >= 85 && rep <= 3) {
      dDom = 1; dCont = rep <= 1 ? 1 : 0;
    }
    return { domestic: CLAMP(club.domesticReputation + dDom, 0, 5), continental: CLAMP(club.continentalReputation + dCont, 0, 5) };
  }

  /* Seleção --------------------------------------------------------- */
  const NATIONAL = {
    minOvrByIntRep: [60, 70, 74, 78, 80, 83],       // OVR mínimo p/ convocação
    baseOvrByIntRep: [70, 75, 77, 80, 83, 85],       // OVR base dos companheiros
    continentalWinByContRep: [1e-5, .02, .05, .1, .2, .3, .8],
    worldCupWinByFifaRep: [1e-6, .005, .05, .08, .12, .18],
    worldCupSelectionByContRep: [.05, .5, .8, 1, 1, 1, 1]
  };
  const everyFour = (age, start) => age >= start && (age - start) % 4 === 0;

  /* Eventos de carreira --------------------------------------------- */
  const EVENT_KEYS = ['training_extra', 'personal_coach', 'mysterious_substance', 'honesty_test', 'indecent_proposal',
    'controversial_post', 'season_load', 'position_change', 'position_competition', 'unexpected_prospect',
    'club_priority', 'rival_offer', 'club_crisis', 'fan_backlash', 'return_home', 'giant_tattoo', 'tax_trouble',
    'foreign_grandfather', 'finish_high_school', 'controversial_statement', 'triumphant_return',
    'club_national_team_conflict', 'injury_at_peak', 'injury', 'decisive_penalty'];
  const EVENT_WEIGHT = {
    giant_tattoo: 35, finish_high_school: 35, fan_backlash: 80, rival_offer: 80, club_crisis: 45,
    unexpected_prospect: 45, return_home: 45, controversial_statement: 45, tax_trouble: 25,
    foreign_grandfather: 25, mysterious_substance: 20, honesty_test: 20, indecent_proposal: 20,
    controversial_post: 35, club_national_team_conflict: 20, injury_at_peak: 20, decisive_penalty: 20,
    triumphant_return: 50
  };
  const EVENT_OPTIONS = {
    training_extra: ['accept', 'reject'], personal_coach: ['accept', 'reject'], mysterious_substance: ['consume', 'reject'],
    honesty_test: ['accept', 'reject'], indecent_proposal: ['proceed', 'reject'], controversial_post: ['support_family', 'support_club'],
    season_load: ['accept', 'stay_calm'], position_change: ['accept', 'reject'], position_competition: ['compete'],
    unexpected_prospect: ['mentor', 'search_exit'], club_priority: ['prioritize_league', 'prioritize_continental'],
    rival_offer: ['accept', 'reject'], club_crisis: ['stay_and_fight', 'search_exit'], fan_backlash: ['stay_and_fight', 'search_exit'],
    return_home: ['stay_abroad', 'return_home'], giant_tattoo: ['accept', 'reject'], tax_trouble: ['stay_and_fight', 'search_exit'],
    foreign_grandfather: ['switch_national_team', 'keep_national_team'], finish_high_school: ['accept', 'reject'],
    controversial_statement: ['apologize'], triumphant_return: [], club_national_team_conflict: ['go_anyway', 'comply'],
    injury_at_peak: ['play_injured', 'recover'], injury: ['continue'], decisive_penalty: ['left', 'right']
  };
  const VARIANTS = {
    training_extra: [{ key: 'preseason_camp', weight: 100 }],
    personal_coach: [{ key: 'nutrition_plan', weight: 100 }],
    controversial_post: [{ key: 'uncle', weight: 1 }, { key: 'aunt', weight: 1 }, { key: 'male_cousin', weight: 1 }, { key: 'female_cousin', weight: 1 }, { key: 'brother', weight: 1 }, { key: 'sister', weight: 1 }],
    season_load: [{ key: 'double_session', weight: 100 }]
  };

  // Modificadores neutros (cada evento devolve um destes alterado)
  function neutralModifiers() {
    return {
      immediateOverallDelta: 0, permanentOverallDelta: 0, statsMultiplier: 1, roleShift: 0,
      suspended: false, forceZeroAppearances: false, deferredOverallDelta: 0, deferredOverallDeltaAfterSeasons: 0,
      roleOverride: undefined, roleOverrideSeasons: 0,
      leagueTrophyProbabilityMultiplier: 1, domesticCupTrophyProbabilityMultiplier: 1,
      continentalPrimaryTrophyProbabilityMultiplier: 1, continentalSecondaryTrophyProbabilityMultiplier: 1,
      clubWorldCupTrophyProbabilityMultiplier: 1,
      nationalTournament: undefined, nationalTournamentParticipation: undefined
    };
  }

  // Efeitos exatos de cada escolha (porte de Ci do Copero)
  function applyEventEffects(rng, eventKey, optionKey, params, currentRole) {
    params = params || {};
    const m = neutralModifiers();
    const forced = params.forcedOutcome;              // 'positive' | 'negative' | undefined
    let c = rng, kind;
    const rollTo = (p, desired) => forced ? { rng: c, success: forced === desired } : RNG.chance(c, p);
    let r;

    if (eventKey === 'training_extra' && optionKey === 'accept') {
      const camp = params.variantKey === 'preseason_camp';
      r = rollTo(camp ? 0.65 : 0.7, 'positive'); c = r.rng;
      m.immediateOverallDelta = r.success ? (camp ? 4 : 3) : (camp ? -3 : -2);
      kind = r.success ? 'positive' : 'negative';
    }
    if (eventKey === 'personal_coach' && optionKey === 'accept') {
      const nut = params.variantKey === 'nutrition_plan';
      r = rollTo(nut ? 0.6 : 0.5, 'positive'); c = r.rng;
      m.permanentOverallDelta = r.success ? (nut ? 3 : 2) : -2;
      kind = r.success ? 'positive' : 'negative';
    }
    if (eventKey === 'mysterious_substance' && optionKey === 'consume') {
      r = rollTo(0.25, 'negative'); c = r.rng;
      kind = r.success ? 'negative' : 'positive';
      m.immediateOverallDelta = r.success ? 0 : 5;
      if (r.success) m.suspended = true;
    }
    if (eventKey === 'honesty_test' && optionKey === 'accept') {
      r = rollTo(0.5, 'negative'); c = r.rng;
      kind = r.success ? 'negative' : 'positive';
      m.immediateOverallDelta = r.success ? 0 : 2;
      if (r.success) m.suspended = true;
    }
    if (eventKey === 'indecent_proposal' && optionKey === 'proceed') {
      r = rollTo(0.5, 'negative'); c = r.rng;
      kind = r.success ? 'negative' : 'positive';
      m.immediateOverallDelta = r.success ? -2 : 2;
      if (r.success) { m.roleOverride = 'substitute'; m.roleOverrideSeasons = 1; }
    }
    if (eventKey === 'controversial_post' && optionKey === 'support_family') {
      m.roleOverrideSeasons = 1;
      if (currentRole === 'starter' || currentRole === 'high_rotation') m.roleOverride = 'low_rotation';
      else if (currentRole === 'low_rotation') m.roleOverride = 'substitute';
      else { m.roleOverride = currentRole; m.forceZeroAppearances = true; }
      kind = 'negative';
    }
    if (eventKey === 'controversial_post' && optionKey === 'support_club') {
      m.immediateOverallDelta = -2; m.deferredOverallDelta = 2; m.deferredOverallDeltaAfterSeasons = 1; kind = 'negative';
    }
    if (eventKey === 'injury' && optionKey === 'continue') {
      m.immediateOverallDelta = injuryOvr(params.injuryType || 'hamstring');
      m.roleOverride = 'substitute'; kind = 'negative';
    }
    if (eventKey === 'season_load' && optionKey === 'accept') {
      const dbl = params.variantKey === 'double_session';
      r = rollTo(dbl ? 0.65 : 0.7, 'positive'); c = r.rng;
      m.roleOverride = r.success ? 'starter' : 'substitute';
      kind = r.success ? 'positive' : 'negative';
    }
    if (eventKey === 'season_load' && optionKey === 'stay_calm') m.roleShift = -1;
    if (eventKey === 'position_change' && optionKey === 'accept') { m.roleOverride = 'starter'; m.immediateOverallDelta = -2; m.deferredOverallDelta = 2; }
    if (eventKey === 'position_change' && optionKey === 'reject') { m.roleShift = -1; kind = 'negative'; }
    if (eventKey === 'position_competition' && optionKey === 'compete') {
      r = rollTo(0.5, 'positive'); c = r.rng;
      m.roleOverride = r.success ? 'starter' : 'low_rotation';
      kind = r.success ? 'positive' : 'negative';
    }
    if (eventKey === 'unexpected_prospect' && optionKey === 'mentor') {
      m.roleShift = -1;
      m.leagueTrophyProbabilityMultiplier = 2; m.domesticCupTrophyProbabilityMultiplier = 2;
      m.continentalPrimaryTrophyProbabilityMultiplier = 2; m.continentalSecondaryTrophyProbabilityMultiplier = 2;
      m.clubWorldCupTrophyProbabilityMultiplier = 2;
    }
    if (eventKey === 'club_priority' && optionKey === 'prioritize_league') { m.leagueTrophyProbabilityMultiplier = 2; m.continentalPrimaryTrophyProbabilityMultiplier = 0.5; }
    if (eventKey === 'club_priority' && optionKey === 'prioritize_continental') { m.leagueTrophyProbabilityMultiplier = 0.5; m.continentalPrimaryTrophyProbabilityMultiplier = 2; }
    if (eventKey === 'rival_offer' && optionKey === 'accept') {
      m.roleOverride = 'high_rotation';
      m.leagueTrophyProbabilityMultiplier = 2; m.domesticCupTrophyProbabilityMultiplier = 2;
      m.continentalPrimaryTrophyProbabilityMultiplier = 2; m.continentalSecondaryTrophyProbabilityMultiplier = 2;
      m.clubWorldCupTrophyProbabilityMultiplier = 2;
    }
    if (eventKey === 'club_crisis' && optionKey === 'stay_and_fight') {
      m.leagueTrophyProbabilityMultiplier = .1; m.domesticCupTrophyProbabilityMultiplier = .1;
      m.continentalPrimaryTrophyProbabilityMultiplier = .1; m.continentalSecondaryTrophyProbabilityMultiplier = .1;
      m.clubWorldCupTrophyProbabilityMultiplier = .1; kind = 'negative';
    }
    if (eventKey === 'fan_backlash' && optionKey === 'stay_and_fight') { m.immediateOverallDelta = -2; m.deferredOverallDelta = 2; kind = 'negative'; }
    if (eventKey === 'return_home' && optionKey === 'stay_abroad') { m.immediateOverallDelta = -5; m.deferredOverallDelta = 5; kind = 'negative'; }
    if (eventKey === 'giant_tattoo' && optionKey === 'accept') {
      r = rollTo(0.7, 'positive'); c = r.rng;
      kind = r.success ? 'positive' : 'negative';
      if (r.success) m.permanentOverallDelta = 2; else m.roleOverride = 'substitute';
    }
    if (eventKey === 'tax_trouble' && optionKey === 'stay_and_fight') { m.immediateOverallDelta = -3; m.deferredOverallDelta = 3; kind = 'negative'; }
    if (eventKey === 'finish_high_school' && optionKey === 'accept') { m.permanentOverallDelta = 1; m.roleShift = -1; }
    if (eventKey === 'controversial_statement' && optionKey === 'apologize') { m.roleShift = -1; kind = 'negative'; }
    if (eventKey === 'club_national_team_conflict') {
      if (optionKey === 'go_anyway') { m.roleOverride = 'substitute'; m.nationalTournamentParticipation = 'force'; }
      else if (optionKey === 'comply') m.nationalTournamentParticipation = 'skip';
    }
    if (eventKey === 'injury_at_peak') {
      r = rollTo(optionKey === 'play_injured' ? 0.8 : 0.3, 'positive'); c = r.rng;
      kind = r.success ? 'positive' : 'negative';
      if (optionKey === 'play_injured') m.immediateOverallDelta = -1;
    }
    if (eventKey === 'decisive_penalty') {
      r = rollTo(0.5, 'positive'); c = r.rng;
      kind = r.success ? 'positive' : 'negative';
    }
    return { rng: c, modifiers: m, outcomeKind: kind };
  }

  // Plano de eventos: N eventos entre 22 e 37 sem slots vizinhos
  function buildPlan(rng, mode) {
    const cfg = MODES[mode] || MODES.normal;
    const p = cfg.periodLengthSeasons;
    const start = 16 + Math.ceil(6 / p) * p;
    const slots = [];
    for (let a = start; a <= 37; a += p) slots.push(a);
    const count = _int(rng, cfg.personalEventCount[0], cfg.personalEventCount[1]);
    // combinações de slots com passo >= 2 (sem vizinhos)
    const combos = [];
    (function rec(idx, acc) {
      if (acc.length === count) { combos.push(acc.slice()); return; }
      for (let i = idx; i < slots.length; i++) { acc.push(slots[i]); rec(i + 2, acc); acc.pop(); }
    })(0, []);
    const chosen = RNG.pick(rng, combos.length ? combos : [slots]);
    return {
      rng: chosen.rng,
      plan: { targetCount: chosen.item.length, slotAges: chosen.item.slice(), completedEventKeys: [], completedSlotAges: [], completedEventAges: [], injuryCount: 0 }
    };
  }

  /* ============================================================
     3 · SELEÇÃO DE EVENTO
     ============================================================ */
  // playerCtx: { age, role, position, overall, nationality:{...} }
  // world: { currentTeam, countryTeams:[...], anyJoinable:bool, rivalTeams:[...], homeCountryTeams:[...],
  //          foreignCountryTeams:[...], alternativeNationalities:[...], upcomingTournaments:[...],
  //          lastSeasonTrophy:bool, injuryAtPeakTrophy:bool, decisiveTrophy:bool }
  function eligibleEvents(ctx, world) {
    const role = ctx.role, pos = ctx.position, age = ctx.age;
    return EVENT_KEYS.filter((k) => {
      if (k === 'season_load' || k === 'position_competition') return role === 'starter' || role === 'high_rotation';
      if (k === 'unexpected_prospect') return age > 22 && (role === 'starter' || role === 'high_rotation') && world.anyJoinable;
      if (k === 'club_priority') return role === 'starter' && (world.currentTeam?.domesticReputation ?? 0) > 2 && (world.currentTeam?.internationalReputation ?? 0) > 2;
      if (k === 'rival_offer') return role === 'starter' && (world.currentTeam?.domesticReputation ?? 0) > 2 && (world.currentTeam?.internationalReputation ?? 0) > 2 && (world.rivalTeams?.length > 0);
      if (k === 'club_crisis') return !!(world.currentTeam && (world.currentTeam.domesticReputation > 1 || world.currentTeam.internationalReputation > 1) && world.anyJoinable);
      if (k === 'fan_backlash') return age > 22 && world.anyJoinable;
      if (k === 'return_home') return age > 24 && (world.homeCountryTeams?.length > 0);
      if (k === 'tax_trouble') return (world.foreignCountryTeams?.length > 0);
      if (k === 'foreign_grandfather') return (world.alternativeNationalities?.length > 0);
      if (k === 'triumphant_return') return !!world.triumphantReturnTeam;
      if (k === 'club_national_team_conflict') {
        const min = NATIONAL.minOvrByIntRep[CLAMP(ctx.nationality?.internationalReputation ?? 0, 0, 5)];
        return ctx.overall >= min && (world.upcomingTournaments || []).some(t => t.selectionQualified);
      }
      if (k === 'injury_at_peak') return role === 'starter' && !!world.injuryAtPeakTrophy;
      if (k === 'decisive_penalty') return !!world.decisiveTrophy;
      if (k === 'position_change') return pos !== 'GK' && pos !== 'GOL';
      return true;
    });
  }

  // Escolhe um evento (uma vez por slot) ou lesão. Devolve {rng, event|null}
  function rollEvent(rng, ctx, plan, world, customKeys) {
    const keys = customKeys || EVENT_KEYS;
    const age = ctx.age;
    if (age === undefined || age > 37) return { rng, event: null };
    if (!plan) return { rng, event: null };
    if (plan.completedEventKeys.length >= plan.targetCount) return { rng, event: null };
    const slot = plan.slotAges.find(a => a <= age && !plan.completedSlotAges.includes(a));
    if (slot === undefined) return { rng, event: null };
    const last = plan.completedEventAges[plan.completedEventAges.length - 1];
    const gap = (MODES.normal.periodLengthSeasons) * 2; // ajustado no adapter por modo
    if (last !== undefined && age - last < (world.periodGap ?? gap)) return { rng, event: null };

    const remaining = keys.filter(k => k !== 'injury' && !plan.completedEventKeys.includes(k));
    const c = remaining.filter(k => eligibleEvents(ctx, world).includes(k));
    const canInjury = keys.includes('injury') && (plan.injuryCount ?? 0) < MAX_INJURIES_PER_CAREER;

    if (canInjury) {
      const inj = RNG.chance(RNG.fork(rng, 'injury:' + (ctx.step ?? 0)), INJURY_CHANCE);
      if (inj.success) {
        const b = RNG.weighted(inj.rng, INJURIES.map(x => ({ item: x, weight: x.weight })));
        return {
          rng: b.rng,
          event: { type: 'career_event', age, eventKey: 'injury', injuryType: b.item.type, slotAge: slot, options: EVENT_OPTIONS.injury.slice() }
        };
      }
      rng = inj.rng;
    }
    if (!c.length) return { rng, event: null };

    const w = RNG.weighted(rng, c.map(k => ({ item: k, weight: EVENT_WEIGHT[k] ?? 100 })));
    rng = w.rng;
    const key = w.item;
    const variants = VARIANTS[key];
    let variantKey;
    if (variants) {
      const v = RNG.weighted(RNG.fork(rng, 'variant:' + (ctx.step ?? 0) + ':' + key), variants.map(x => ({ item: x.key, weight: x.weight })));
      variantKey = v.item;
    }
    return { rng, event: { type: 'career_event', age, eventKey: key, variantKey, slotAge: slot, options: (EVENT_OPTIONS[key] || []).slice() } };
  }

  function commitEvent(plan, eventKey, slotAge, age) {
    if (!plan) return plan;
    if (eventKey !== 'injury' && plan.completedEventKeys.includes(eventKey)) return plan;
    if (eventKey === 'injury' && (plan.injuryCount ?? 0) >= MAX_INJURIES_PER_CAREER) return plan;
    return {
      ...plan,
      completedEventKeys: [...plan.completedEventKeys, eventKey],
      completedSlotAges: [...plan.completedSlotAges, slotAge],
      completedEventAges: [...(plan.completedEventAges || []), age],
      injuryCount: eventKey === 'injury' ? (plan.injuryCount ?? 0) + 1 : plan.injuryCount
    };
  }

  /* ============================================================
     4 · DESENVOLVIMENTO / CICLO DE OVR
     ============================================================ */
  function devRange(profile, gk, age) {
    // Como no Copero a tabela só cobre 18..38: fora disso não existe faixa (nem desenvolvimento)
    const t = gk ? DEV_GK : (DEV[profile] || DEV.normal);
    return t[age];
  }
  function devDelta(rng, ctx, targetAge, role, mode) {
    // ctx: { age, position(GK?), profile }
    const gk = isGk(ctx.position);
    const range = devRange(ctx.profile, gk, targetAge);
    if (!range) return null;
    const first = _int(rng, range[0], range[1]);
    let p = first.rng, v = first.value;
    const penalty = Math.floor((targetAge - 16) / 2) >= 4 && (isLowRotation(role) || isBench(role));
    if (penalty) {
      const second = _int(p, range[0], range[1]);
      p = second.rng; v = Math.min(first.value, second.value);
    }
    return { rng: p, delta: mode === 'highroll' ? range[1] : v };
  }
  function newCycle(rng, ctx, role, mode) {
    const targetAge = ctx.age % 2 === 0 ? ctx.age + 2 : ctx.age + 1;
    const d = devDelta(rng, ctx, targetAge, role, mode);
    if (!d) return { rng, cycle: null };
    const l = d.delta, s = Math.abs(l);
    if (s === 0) return { rng: d.rng, cycle: { targetAge, annualDeltas: [0, 0], nextPart: ctx.age % 2 === 0 ? 0 : 1 } };
    const c = s >= 4 ? Math.ceil(s * 0.25) : 0;
    const p = s >= 4 ? Math.floor(s * 0.75) : s;
    const u = _int(d.rng, c, p);
    const dd = u.value * Math.sign(l);
    return { rng: u.rng, cycle: { targetAge, annualDeltas: [dd, l - dd], nextPart: ctx.age % 2 === 0 ? 0 : 1 } };
  }
  // avança 1 ano; devolve {rng, overall, cycle}  (ordem dos argumentos igual à do Copero)
  function advanceOverall(rng, ctx, cycle, suspended, role, mode) {
    const targetAge = ctx.age % 2 === 0 ? ctx.age + 2 : ctx.age + 1;
    let c = (cycle && cycle.targetAge === targetAge) ? { rng, cycle } : newCycle(rng, ctx, role, mode);
    if (!c.cycle) return { rng: c.rng, overall: ctx.overall, cycle: null };
    const part = c.cycle.nextPart;
    const raw = c.cycle.annualDeltas[part];
    const delta = (suspended && raw > 0) ? 0 : raw;
    return {
      rng: c.rng,
      overall: CLAMP(ctx.overall + delta, 40, 99),
      cycle: part === 0 ? { ...c.cycle, nextPart: 1 } : null
    };
  }

  /* ============================================================
     5 · ESTATÍSTICAS DA TEMPORADA
     ============================================================ */
  function seasonStats(rng, ctx) {
    // ctx: { overall, position, role, clubStrengthRep, appearanceMultiplier, statsMultiplier, scoringMultiplier, forceZero }
    const gk = isGk(ctx.position);
    const role = ctx.role;
    const range = appearanceRange(role, gk);
    const a = _int(rng, range[0], range[1]);
    let p = a.rng;
    const apps = (ctx.forceZero) ? 0 : Math.round(a.value * (ctx.appearanceMultiplier ?? 1));
    const diff = ctx.overall - baseOvrOf(ctx.clubStrengthRep);

    if (gk) {
      const strength = [1.4, 1.3, 1.1, .9, .7, .5][CLAMP(ctx.clubStrengthRep, 0, 5)];
      const jitter = _num(p, 0.9, 1.1); p = jitter.rng;
      const conceded = Math.max(0, Math.round(apps * strength * gkConcededMult(diff) * jitter.value));
      const clean = apps === 0 ? 0 : Math.max(0, Math.round(apps * CLAMP(.42 - conceded / Math.max(1, apps) * .12, .05, .5)));
      return { rng: p, stats: { appearances: apps, goals: 0, assists: 0, cleanSheets: Math.max(0, Math.round(clean * (ctx.statsMultiplier ?? 1))), goalsConceded: Math.max(0, Math.round(conceded * (ctx.statsMultiplier ?? 1))) } };
    }
    const band = bandOf(diff);
    const sMult = teamStrengthMult(ctx.clubStrengthRep);
    const fin = finishingMult(ctx.overall);
    const jitter = _num(p, 0.9, 1.1); p = jitter.rng;
    const goals = Math.max(0, Math.round(apps * GOAL_RATE[ctx.roleGroup][band] * sMult * jitter.value * (ctx.statsMultiplier ?? 1) * fin * (ctx.scoringMultiplier ?? 1)));
    const assists = Math.max(0, Math.round(apps * ASSIST_RATE[ctx.roleGroup][band] * sMult * jitter.value * (ctx.statsMultiplier ?? 1) * fin * (ctx.scoringMultiplier ?? 1)));
    return { rng: p, stats: { appearances: apps, goals, assists, cleanSheets: 0, goalsConceded: 0 } };
  }

  /* ============================================================
     6 · TÍTULOS
     ============================================================ */
  function luckMult(diff) { return diff >= 10 ? 1.6 : diff >= 6 ? 1.3 : diff >= 3 ? 1.1 : 1; }

  // club: { internationalReputation, domesticReputation, continentalReputation, confederation, tier }
  // prevSeason, lastSeason — para regra da secundária
  function simulateTrophies(rng, player, club, modifiers, prevSeasonSameClub, forced) {
    modifiers = modifiers || neutralModifiers();
    const diff = player.overall - baseOvrOf(club.internationalReputation);
    const p = luckMult(diff);
    const rep = effectiveRep(player.overall, club);
    const dom = rep.domestic, cont = rep.continental;
    const confed = (club.confederation || '').toUpperCase();

    const list = [];
    const leagueProb = PROB.league[CLAMP(dom, 0, 5)] * modifiers.leagueTrophyProbabilityMultiplier;
    const cupProb = PROB.cup[CLAMP(dom, 0, 5)] * modifiers.domesticCupTrophyProbabilityMultiplier;
    if (!club.tier || club.tier === 1) list.push(['league', leagueProb]);
    if (cupProb > 0) list.push(['cup', cupProb]);
    if (club.tier === 1) {
      list.push(['continental_primary', PROB.continentalPrimary[CLAMP(cont, 0, 5)] * modifiers.continentalPrimaryTrophyProbabilityMultiplier]);
      if (CONFEDS_WITH_SECONDARY.has(confed)) list.push(['continental_secondary', PROB.continentalSecondary[CLAMP(cont, 0, 5)] * modifiers.continentalSecondaryTrophyProbabilityMultiplier]);
      if (clubWorldCupYear(player.age)) {
        const cwc = (PROB.clubWorldCupByConfederation[confed] || [])[CLAMP(cont, 0, 5)] ?? 0;
        list.push(['club_world_cup', cwc * modifiers.clubWorldCupTrophyProbabilityMultiplier]);
      }
    }

    const won = [];
    let c = rng, wonPrimary = false;
    const lastTrophies = prevSeasonSameClub || [];
    const lastHadLeague = lastTrophies.includes('league');
    const lastHadPrimary = lastTrophies.includes('continental_primary');
    const lastHadSecondary = lastTrophies.includes('continental_secondary');

    for (const [name, probRaw] of list) {
      if (name === 'continental_secondary') {
        const suppress = wonPrimary || lastHadLeague || lastHadPrimary || lastHadSecondary;
        if (suppress && forced?.trophy !== 'continental_secondary') continue;
      }
      const prob = (forced && forced.trophy === name && forced.result === 'skip') ? 0 : Math.min(1, probRaw * p);
      const roll = (forced && forced.trophy === name && forced.result === 'force') ? { rng: c, success: true } : RNG.chance(c, prob);
      c = roll.rng;
      if (roll.success) { won.push(name); if (name === 'continental_primary') wonPrimary = true; }
    }
    return { rng: c, trophies: won };
  }

  /* Prêmios individuais --------------------------------------------- */
  function awardChance(ovr, trophies) {
    const hasLeague = trophies.includes('league');
    const hasPrimary = trophies.includes('continental_primary');
    if (ovr >= 97) return 1;
    if (ovr >= 94) return hasLeague && hasPrimary ? 1 : hasPrimary ? .8 : hasLeague ? .65 : .5;
    if (ovr >= 90) return hasLeague && hasPrimary ? .6 : hasPrimary ? .4 : hasLeague ? .3 : .2;
    if (ovr >= 85) return hasLeague && hasPrimary ? .1 : hasPrimary ? .05 : hasLeague ? .01 : 0;
    return 0;
  }
  const roleAwardMult = (group) => group === 'support' ? .5 : group === 'defensive' ? .25 : 1;
  const isStarterish = (r) => r === 'starter' || r === 'high_rotation';
  function goldenBootChance(stats, isUefa) {
    if (!isUefa) return 0;
    if (stats.goals >= 50) return 1;
    if (stats.goals >= 40) return .5;
    if (stats.goals >= 30) return .25;
    return 0;
  }
  function simulateAwards(rng, player, stats, trophies, club, role, prevSeasonExists) {
    const awards = [];
    const confed = (club.confederation || '').toUpperCase();
    const gk = isGk(player.position);
    const chance = isStarterish(role) ? awardChance(player.overall, trophies) * (gk ? 1 : roleAwardMult(player.roleGroup)) : 0;
    const r = RNG.chance(rng, chance);
    let c = r.rng;
    if (r.success) awards.push(gk ? 'golden_glove' : 'ballon_dor');
    if (!gk) {
      const g = RNG.chance(c, goldenBootChance(stats, confed === 'UEFA'));
      c = g.rng;
      if (g.success) awards.push('golden_boot');
    }
    return { rng: c, awards };
  }

  /* ============================================================
     7 · SELEÇÃO (torneios e títulos)
     ============================================================ */
  function scheduleTournaments(rng, nationality, fromAge, seasons) {
    const out = [];
    let c = rng;
    for (let i = 0; i < seasons; i++) {
      const age = fromAge + i;
      if (everyFour(age, 17)) out.push({ trophy: 'national_continental', age, selectionQualified: true });
      if (everyFour(age, 19)) {
        const rep = CLAMP(nationality.continentalReputation ?? 0, 0, NATIONAL.worldCupSelectionByContRep.length - 1);
        const r = RNG.chance(c, NATIONAL.worldCupSelectionByContRep[rep]); c = r.rng;
        out.push({ trophy: 'world_cup', age, selectionQualified: r.success });
      }
    }
    return { rng: c, tournaments: out };
  }
  function nationalTournamentResult(rng, player, nationality, tournaments, modifiers) {
    modifiers = modifiers || neutralModifiers();
    if (modifiers.suspended) return { rng, trophies: [], calledUp: false };
    const cont = tournaments.find(t => t.age === player.age && t.trophy === 'national_continental');
    const wc = tournaments.find(t => t.age === player.age && t.trophy === 'world_cup');
    const qualifiedCont = !!cont?.selectionQualified;
    const qualifiedWc = !!wc?.selectionQualified;
    if (!qualifiedCont && !qualifiedWc) return { rng, trophies: [], calledUp: false };

    const minOvr = NATIONAL.minOvrByIntRep[CLAMP(nationality.internationalReputation ?? 0, 0, 5)];
    const skipping = modifiers.nationalTournamentParticipation === 'skip';
    if (skipping || (player.overall < minOvr && modifiers.nationalTournamentParticipation !== 'force')) {
      return { rng, trophies: [], calledUp: false };
    }
    let c = rng; const won = [];
    if (qualifiedCont) {
      const rep = CLAMP(nationality.continentalReputation ?? 0, 0, NATIONAL.continentalWinByContRep.length - 1);
      const r = RNG.chance(c, NATIONAL.continentalWinByContRep[rep]); c = r.rng;
      const force = modifiers?.nationalTrophyOverride?.trophy === 'national_continental';
      const ok = force ? modifiers.nationalTrophyOverride.result === 'force' : r.success;
      if (ok) won.push('national_continental');
    }
    if (qualifiedWc) {
      const rep = CLAMP(nationality.fifaReputation ?? 0, 0, NATIONAL.worldCupWinByFifaRep.length - 1);
      const r = RNG.chance(c, NATIONAL.worldCupWinByFifaRep[rep]); c = r.rng;
      const force = modifiers?.nationalTrophyOverride?.trophy === 'world_cup';
      const ok = force ? modifiers.nationalTrophyOverride.result === 'force' : r.success;
      if (ok) won.push('world_cup');
    }
    return { rng: c, trophies: won, calledUp: true };
  }

  /* ============================================================
     8 · PROPOSTAS / TRANSFERÊNCIAS
     ============================================================ */
  // Regras de origem de clube: país do clube, jogador, mesmo país/confederação
  function offerWeights(ovr) {
    if (ovr >= 83) return { countryClub: 0, countryPlayer: 0, confederationClub: 0, confederationPlayer: 0, random: 100 };
    if (ovr >= 78) return { countryClub: 0, countryPlayer: 0, confederationClub: 25, confederationPlayer: 25, random: 50 };
    if (ovr >= 73) return { countryClub: 0, countryPlayer: 0, confederationClub: 50, confederationPlayer: 50, random: 0 };
    if (ovr >= 50) return { countryClub: 50, countryPlayer: 50, confederationClub: 0, confederationPlayer: 0, random: 0 };
    return { countryClub: 0, countryPlayer: 0, confederationClub: 0, confederationPlayer: 0, random: 0 };
  }
  function reputationJitter(rng, target) {
    const r = _num(rng, 0, 1);
    let rep;
    if (target === -1) rep = r.value < .8 ? -1 : 0;
    else if (target === 5) rep = r.value < .8 ? 5 : 4;
    else rep = r.value < .1 ? target + 1 : r.value < .9 ? target : target - 1;
    return { rng: r.rng, reputation: CLAMP(rep, -1, 5) };
  }
  // clubPool: [{id, confederation, countryFifaCode, internationalReputation, domesticReputation, continentalReputation, ...}]
  function generateTransferOffers(rng, player, currentClub, clubPool, count) {
    count = count || 2;
    const used = new Set([currentClub.id]);
    const picks = [];
    let c = rng;
    const target = offerReputation(player.overall);
    const pool = clubPool.filter(x => !used.has(x.id));
    const sameCountry = pool.filter(x => x.countryFifaCode === currentClub.countryFifaCode);
    const sameConfed = pool.filter(x => x.countryFifaCode !== currentClub.countryFifaCode && x.confederation === currentClub.confederation);
    while (picks.length < count) {
      const j = reputationJitter(c, target); c = j.rng;
      const candidates = pool.filter(x => x.internationalReputation === j.reputation && !used.has(x.id));
      if (!candidates.length) break;
      // pondera país do clube / país do jogador / confederação
      const w = offerWeights(player.overall);
      const weighted = candidates.map(x => {
        let weight = w.random;
        if (x.countryFifaCode === currentClub.countryFifaCode) weight += w.countryClub;
        if (x.countryFifaCode === player.nationality?.fifaCode) weight += w.countryPlayer;
        if (x.confederation === currentClub.confederation) weight += w.confederationClub;
        if (x.confederation === player.nationality?.confederation) weight += w.confederationPlayer;
        return { item: x, weight };
      }).filter(x => x.weight > 0);
      if (!weighted.length) break;
      const r = RNG.weighted(c, weighted); c = r.rng;
      picks.push(r.item); used.add(r.item.id);
    }
    return { rng: c, teams: picks };
  }
  // Empréstimo: clubes mais fracos, mesmo país/confederação
  function generateLoanOffers(rng, player, currentClub, clubPool, count) {
    count = count || 3;
    const used = new Set([currentClub.id]);
    const out = [];
    let c = rng;
    const target = offerReputation(player.overall);
    const sameCountry = clubPool.filter(x => x.countryFifaCode === currentClub.countryFifaCode && !used.has(x.id) && x.internationalReputation <= target);
    const sameConfed = clubPool.filter(x => x.countryFifaCode !== currentClub.countryFifaCode && x.confederation === currentClub.confederation && !used.has(x.id) && x.internationalReputation <= target);
    if (!sameCountry.length && !sameConfed.length) return { rng: c, teams: [] };
    while (out.length < count) {
      const choose = RNG.weighted(c, [{ item: sameCountry, weight: sameCountry.length ? 90 : 0 }, { item: sameConfed, weight: sameConfed.length ? 10 : 0 }]);
      c = choose.rng;
      const list = choose.item.filter(x => !used.has(x.id));
      if (!list.length) break;
      const r = RNG.pick(c, list); c = r.rng;
      out.push(r.item); used.add(r.item.id);
    }
    return { rng: c, teams: out };
  }
  // Não-renovação: clubes por reputação, priorizando mesmo país
  function generateNonRenewalOffers(rng, player, contractClub, pool, count) {
    count = count || (player.age >= 32 ? 2 : 3);
    const used = new Set([contractClub.id]);
    const out = [];
    let c = rng;
    while (out.length < count) {
      const jitter = reputationJitter(c, player.offerReputation ?? offerReputation(player.overall)); c = jitter.rng;
      let list = pool.filter(x => x.internationalReputation <= Math.max(jitter.reputation, player.offerReputation ?? 0) && !used.has(x.id));
      // tenta descer de reputação
      if (!list.length) break;
      const r = RNG.pick(c, list); c = r.rng;
      out.push(r.item); used.add(r.item.id);
    }
    return { rng: c, teams: out };
  }
  const lowRoleStreakNeeded = (mode) => (MODES[mode] || MODES.normal).lowRotationBeforeNonRenewal;
  const benchStreakNeeded = (mode) => (MODES[mode] || MODES.normal).substituteBeforeNonRenewal;

  /* ============================================================
     9 · CONQUISTAS (achievements)
     ============================================================ */
  const ACHIEVEMENTS = [
    { code: 'king_of_america', pt: 'Rei da América', desc: 'Ganhe Copa América e Copa Libertadores em uma carreira.' },
    { code: 'one_club_legend', pt: 'Lenda do clube', desc: 'Jogue toda a carreira em um só clube e ganhe Copa, Liga e o torneio continental.' },
    { code: 'europe_owner', pt: 'Dono da Europa', desc: 'Ganhe as cinco grandes ligas europeias em uma carreira.' },
    { code: 'mr_champions', pt: 'Mr. Champions', desc: 'Ganhe cinco títulos de Champions.' },
    { code: 'goat', pt: 'GOAT', desc: 'Ganhe uma Copa do Mundo, dois títulos continentais de seleções, oito Bolas de Ouro e quatro títulos de Champions.' },
    { code: 'only_pele', pt: 'Só o Pelé', desc: 'Ganhe três Copas do Mundo e faça mais de 1000 gols.' },
    { code: 'black_spider', pt: 'Aranha Negra', desc: 'Ganhe seis prêmios de melhor goleiro do ano.' },
    { code: 'net_terror', pt: 'Terror das redes', desc: 'Ganhe seis Chuteiras de Ouro.' },
    { code: 'complete_football', pt: 'Completar o futebol', desc: 'Conquiste todos os grandes títulos e prêmios de clube e seleção.' },
    { code: 'most_decorated', pt: 'O mais vencedor da história', desc: 'Ganhe 49 títulos coletivos ou mais.' },
    { code: 'ringless', pt: 'Ringless', desc: 'Termine uma carreira sem títulos coletivos.' },
    { code: 'national_hero', pt: 'Herói nacional', desc: 'Ganhe a Copa do Mundo com uma seleção que nunca venceu.' },
    { code: 'the_world_is_yours', pt: 'O mundo é seu', desc: 'Ganhe a Copa do Mundo e o Mundial de Clubes.' },
    { code: 'from_the_periphery', pt: 'Da periferia', desc: 'Ganhe uma Bola de Ouro com um país da África, Ásia, América do Norte, América Central ou Oceania.' },
    { code: 'ushuaia_to_darien', pt: 'De Ushuaia a Darién', desc: 'Jogue nas dez ligas nacionais da América do Sul.' },
    { code: 'nomad', pt: 'Nômade', desc: 'Jogue em clubes dos seis continentes.' },
    { code: 'from_the_bottom', pt: 'De baixo', desc: 'Chegue a ganhar a liga partindo de uma terceira divisão com o mesmo clube.' },
    { code: 'matagigantes', pt: 'Matagigantes', desc: 'Ganhe Libertadores ou Champions com um clube pequeno.' },
    { code: 'the_treble', pt: 'A tríplice coroa', desc: 'Ganhe Liga, Copa e torneio continental em uma temporada.' },
    { code: 'baldosero', pt: 'Baldosero', desc: 'Jogue por 24 clubes diferentes em uma mesma carreira.' }
  ];
  const BIG5 = new Set(['ESP', 'FRA', 'ENG', 'ITA', 'GER']);
  const WORLD_CHAMPIONS = new Set(['BRA', 'ITA', 'GER', 'ARG', 'ESP', 'FRA', 'URU', 'ENG']);
  const NON_EUROPE_STRONG = new Set(['CAF', 'AFC', 'OFC', 'CONCACAF']);
  const SA_LEAGUES = 10;

  // seasons: [{ teamId, trophies:[], awards:[], competitionTier, nationalityFifaCode, confederation }]
  // ctx: { mode, phase, totalsGoals, nationality:{fifaCode, confederation} }
  function computeAchievements(seasons, ctx) {
    const got = new Set();
    if (!seasons.length) return got;
    const nat = ctx.nationality || {};
    const natConf = nat.confederation || null;
    const wc = seasons.filter(s => s.trophies.includes('world_cup'));
    const uefaPrimary = seasons.filter(s => s.trophies.includes('continental_primary') && s.confederation === 'UEFA');
    const conmebolPrimary = seasons.filter(s => s.trophies.includes('continental_primary') && s.confederation === 'CONMEBOL');
    const ballons = seasons.filter(s => s.awards.includes('ballon_dor'));
    const boots = seasons.filter(s => s.awards.includes('golden_boot'));
    const gloves = seasons.filter(s => s.awards.includes('golden_glove'));
    const natCont = seasons.filter(s => s.trophies.includes('national_continental'));
    // O Copero classifica o torneio de seleção pela confederação do jogador
    // (nationality_fifa_code), e não pela confederação do clube da temporada.
    const natContConmebol = natConf === 'CONMEBOL' ? natCont : [];
    const natContUefa = natConf === 'UEFA' ? natCont : [];

    if (natContConmebol.length && conmebolPrimary.length) got.add('king_of_america');
    if (uefaPrimary.length >= 5) got.add('mr_champions');
    if (wc.length && (natContConmebol.length >= 2 || natContUefa.length >= 2) && ballons.length >= 8 && uefaPrimary.length >= 4) got.add('goat');
    if (wc.length >= 3 && (ctx.totalsGoals || 0) > 1000) got.add('only_pele');
    if (gloves.length >= 6) got.add('black_spider');
    if (boots.length >= 6) got.add('net_terror');
    if (seasons.reduce((a, s) => a + s.trophies.length, 0) >= 49) got.add('most_decorated');
    if (wc.length && seasons.some(s => s.trophies.includes('club_world_cup'))) got.add('the_world_is_yours');
    if (ballons.length && natConf && NON_EUROPE_STRONG.has(natConf)) got.add('from_the_periphery');
    if (wc.some(s => s.nationalityFifaCode && !WORLD_CHAMPIONS.has(s.nationalityFifaCode.toUpperCase()))) got.add('national_hero');
    const big5Won = new Set(seasons.filter(s => s.trophies.includes('league') && s.competitionTier === 1).map(s => s.countryFifaCode).filter(c => c && BIG5.has(c)));
    if (big5Won.size === BIG5.size) got.add('europe_owner');

    const conmebolDouble = seasons.some(s => s.confederation === 'CONMEBOL' && s.trophies.includes('league') && s.trophies.includes('cup'));
    const uefaDouble = seasons.some(s => s.confederation === 'UEFA' && s.trophies.includes('league') && s.trophies.includes('cup'));
    if (wc.length && natCont.length && (natConf === 'CONMEBOL' || natConf === 'UEFA') && conmebolPrimary.length && uefaPrimary.length && conmebolDouble && uefaDouble && ballons.length && boots.length) got.add('complete_football');
    const saCountries = new Set(seasons.filter(s => s.confederation === 'CONMEBOL').map(s => s.countryFifaCode).filter(Boolean));
    if (saCountries.size >= SA_LEAGUES) got.add('ushuaia_to_darien');
    const conts = new Set(seasons.map(s => s.confederation).filter(Boolean));
    if (conts.size >= 6) got.add('nomad');
    const first = seasons[0];
    if (first && first.competitionTier === 3 && seasons.some(s => s.teamId === first.teamId && s.countryFifaCode === first.countryFifaCode && s.competitionTier === 1 && s.trophies.includes('league'))) got.add('from_the_bottom');
    if (seasons.some(s => s.continentalReputation === 0 && s.trophies.includes('continental_primary') && (s.confederation === 'CONMEBOL' || s.confederation === 'UEFA'))) got.add('matagigantes');
    if (seasons.some(s => s.trophies.includes('league') && s.trophies.includes('cup') && s.trophies.includes('continental_primary'))) got.add('the_treble');
    if (ctx.mode === 'long' && new Set(seasons.map(s => s.teamId)).size >= 24) got.add('baldosero');
    if (ctx.phase === 'summary') {
      const sameClub = seasons.every(s => s.teamId === first.teamId);
      const hadTransfer = (ctx.hadTransferLoan || false);
      const cumTrophies = new Set(seasons.flatMap(s => s.trophies));
      if (sameClub && !hadTransfer && cumTrophies.has('league') && cumTrophies.has('cup') && cumTrophies.has('continental_primary')) got.add('one_club_legend');
      if (seasons.every(s => s.trophies.length === 0)) got.add('ringless');
    }
    return got;
  }

  /* ============================================================
     10 · API
     ============================================================ */
  const TROPHY_LABELS = {
    league: 'Liga', cup: 'Copa', continental_primary: 'Continental principal', continental_secondary: 'Continental secundária',
    club_world_cup: 'Mundial de Clubes', national_continental: 'Seleção continental', world_cup: 'Copa do Mundo'
  };
  const AWARD_LABELS = { ballon_dor: 'Bola de Ouro', golden_boot: 'Chuteira de Ouro', golden_glove: 'Luva de Ouro' };
  const NATIONAL_CONTINENTAL_BY_CONFEDERATION = {
    UEFA: 'Eurocopa', CONMEBOL: 'Copa América', CONCACAF: 'Copa Ouro', CAF: 'Copa Africana de Nações', AFC: 'Copa Asiática', OFC: 'Copa das Nações da OFC'
  };

  const MotorCopero = {
    RNG, MODES, RETIRE_AGE, REP_OVR, VALUE_TAB, DEV, DEV_GK, INJURIES, EVENT_KEYS, EVENT_WEIGHT, EVENT_OPTIONS, VARIANTS,
    PROB, NATIONAL, ACHIEVEMENTS, TROPHY_LABELS, AWARD_LABELS, NATIONAL_CONTINENTAL_BY_CONFEDERATION,
    ROLE_GROUPS, ROLE_ORDER, ROLE_ORDER_GK, POS_COPERO, POS_GROUPS,
    baseOvrOf, offerReputation, rollProfile, marketValue, roundValue, ageValueFactor,
    groupOf, isGk, appearanceRange, roleFromDiff, shiftRole, isLowRotation, isBench, appearanceMult,
    bandOf, GOAL_RATE, ASSIST_RATE, teamStrengthMult, finishingMult, gkConcededMult,
    effectiveRep, clubWorldCupYear, injuryOvr,
    neutralModifiers, applyEventEffects, buildPlan, eligibleEvents, rollEvent, commitEvent,
    devRange, devDelta, newCycle, advanceOverall,
    seasonStats, simulateTrophies, simulateAwards, awardChance, goldenBootChance, roleAwardMult,
    scheduleTournaments, nationalTournamentResult, everyFour,
    offerWeights, reputationJitter, generateTransferOffers, generateLoanOffers, generateNonRenewalOffers,
    lowRoleStreakNeeded, benchStreakNeeded,
    computeAchievements
  };

  if (typeof module !== 'undefined' && module.exports) module.exports = MotorCopero;
  global.MotorCopero = MotorCopero;
})(typeof window !== 'undefined' ? window : globalThis);
