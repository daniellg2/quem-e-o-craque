(function (global) {
  'use strict';

  // Tabelas de acesso/rebaixamento do simulador Copero, por OVR e reputação.
  const PROMOTION_2 = [[64,.03],[69,.04],[74,.06],[79,.09],[84,.13],[87,.18],[89,.25],[99,.30]];
  const PROMOTION_3 = [[64,.04],[69,.05],[74,.07],[79,.11],[84,.15],[87,.21],[89,.28],[99,.35]];
  const RELEGATION_2 = [[64,.20],[69,.16],[74,.12],[79,.09],[84,.06],[87,.03],[89,.01],[99,0]];
  const PROMOTION_REP = [1,1.1,1.2,1.3,1.5,1.75,2];
  const RELEGATION_REP = [1,.9,.8,.7,.6,.5,.4];
  const CLUB_TROPHIES = new Set(['league','cup','continental_primary','continental_secondary','club_world_cup']);
  const clamp = (n,a,b) => Math.max(a,Math.min(b,n));
  const band = (ovr,table) => (table.find(([max]) => ovr<=max)||table[table.length-1])[1];

  function links(leagues) {
    const byCountry = new Map(), result = {};
    for (const league of leagues) {
      const code = league.code, country = league.pais || league.countryFifaCode || league.country;
      const tier = Number(league.tier);
      if (!code || !country || !Number.isInteger(tier) || tier<1) continue;
      if (!byCountry.has(country)) byCountry.set(country,new Map());
      const tiers = byCountry.get(country);
      if (!tiers.has(tier)) tiers.set(tier,new Set());
      tiers.get(tier).add(code);
    }
    for (const [country,tiers] of byCountry) for (const [tier,codes] of tiers) for (const code of codes) {
      const single = t => tiers.get(t)?.size===1 ? [...tiers.get(t)][0] : null;
      result[code] = {country,tier,upper:single(tier-1),lower:single(tier+1)};
    }
    return result;
  }

  function resolve({league,overall,internationalReputation=0,domesticReputation=0,suspended=false,trophies=[]},link,draw) {
    if (!link || (!link.upper && !link.lower)) return null;
    const tier=link.tier,rep=clamp(Math.round(internationalReputation),-1,5)+1;
    const wonLeague=trophies.includes('league');
    let kind=null;
    if (wonLeague && link.upper && !suspended) kind='promotion';
    else if (tier===1 && link.lower && !wonLeague) {
      // Copero: clubes fortes domesticamente não são rebaixados pela rolagem.
      let boost=0;
      if (overall>=90) boost=internationalReputation===3?1:internationalReputation<=2?2:0;
      else if (overall>=85 && internationalReputation<=3) boost=1;
      const effectiveDom=domesticReputation+boost;
      if (effectiveDom<1) {
        const factor=overall<=65?.6:overall<=80?.6+(overall-65)/15*.25:overall<=85?.85+(overall-80)/5*.15:overall<=95?1+(overall-85)/10*.1:1.1;
        const chance=clamp(.05+.1*((1.1-factor)/.5),.05,.15);
        if (draw()<chance) kind='relegation';
      }
    } else if (tier===2) {
      const promotion=link.upper&&!suspended?Math.min(.9,band(overall,PROMOTION_2)*PROMOTION_REP[rep]):0;
      const relegation=link.lower?band(overall,RELEGATION_2)*RELEGATION_REP[rep]:0;
      const value=draw();
      if (value<promotion) kind='promotion';
      else if (value<promotion+relegation) kind='relegation';
    } else if (tier>=3 && link.upper && !suspended) {
      if (draw()<Math.min(.9,band(overall,PROMOTION_3)*PROMOTION_REP[rep])) kind='promotion';
    }
    const to=kind==='promotion'?link.upper:kind==='relegation'?link.lower:null;
    if (!to) return null;
    return {kind,from:league,to,fromTier:tier,toTier:tier+(kind==='promotion'?-1:1)};
  }

  function trophiesAfterMovement(trophies,movement) {
    if (!movement) return trophies.slice();
    if (movement.kind==='relegation') return trophies.filter(t=>!CLUB_TROPHIES.has(t));
    return trophies.includes('league')?trophies.slice():[...trophies,'league'];
  }

  const api={links,resolve,trophiesAfterMovement};
  if (typeof module==='object' && module.exports) module.exports=api;
  global.CAREER_DIVISIONS=api;
})(typeof window!=='undefined'?window:globalThis);
