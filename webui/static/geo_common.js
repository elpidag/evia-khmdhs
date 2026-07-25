/* Shared helpers for the "paper" Greece maps (overview + contractor pages).
 * Same visual language as templates/map.html: no tile layer, Eurostat NUTS-3
 * polygons on a plain backdrop, sqrt-normalised sequential shading.
 * Loaded as a classic script; exposes a single global `GeoCommon`.
 */
window.GeoCommon = (function () {
  'use strict';

  // -- formatters (Greek conventions) ------------------------------------
  const fmtEur = n => new Intl.NumberFormat('el-GR',
    { style: 'currency', currency: 'EUR', maximumFractionDigits: 0 }).format(n);
  const fmtEurShort = n => {
    const v = Math.abs(n);
    if (v >= 1e9) return (n / 1e9).toFixed(2).replace('.', ',') + ' B €';
    if (v >= 1e6) return (n / 1e6).toFixed(1).replace('.', ',') + ' M €';
    if (v >= 1e3) return (n / 1e3).toFixed(0) + ' K €';
    return Math.round(n) + ' €';
  };
  const fmtInt = n => new Intl.NumberFormat('el-GR').format(n);

  // -- palettes ----------------------------------------------------------
  // Works side: the YlOrBr ramp already used on the flow map (continuity).
  const RAMP_WORKS = ['#fff7e6', '#feecbd', '#fed692', '#feb84e',
                      '#ef8b1c', '#cc5803', '#992f00', '#6c1a00'];
  // Contractor side: single-hue blue sequential (distinct semantics ⇒
  // distinct hue), steps 100→700 of the validated reference ramp.
  const RAMP_HOME = ['#f2f7fe', '#cde2fb', '#9ec5f4', '#6da7ec',
                     '#3987e5', '#256abf', '#184f95', '#0d366b'];
  const COLORS = {
    landEmpty: '#efe8d7',
    regionStroke: '#9b8e74',
    regionStrokeHover: '#3a3429',
    bubbleWorks: '#b33a1a',
    bubbleWorksStroke: '#6c1a00',
    bubbleHome: '#2a78d6',
    bubbleHomeStroke: '#0d366b',
    homePin: '#0d366b',
  };

  // -- map ---------------------------------------------------------------
  function initPaperMap(elId, opts) {
    const map = L.map(elId, Object.assign({
      zoomSnap: 0.25,
      attributionControl: false,
      zoomControl: true,
      scrollWheelZoom: false,   // page scroll stays usable; zoom via buttons
    }, opts || {})).setView([38.6, 24.2], 6.25);
    map.createPane('regions'); map.getPane('regions').style.zIndex = 350;
    map.createPane('links');   map.getPane('links').style.zIndex = 420;
    map.createPane('bubbles'); map.getPane('bubbles').style.zIndex = 450;
    map.createPane('pins');    map.getPane('pins').style.zIndex = 500;
    map.on('focus', () => map.scrollWheelZoom.enable());
    map.on('blur', () => map.scrollWheelZoom.disable());
    return map;
  }

  // sqrt-normalised index into a ramp; zero → neutral paper.
  function makeChoro(ramp, maxV) {
    return v => {
      if (!v || v <= 0) return COLORS.landEmpty;
      const t = Math.sqrt(v / maxV);
      return ramp[Math.min(ramp.length - 1, Math.max(0, Math.floor(t * ramp.length)))];
    };
  }

  // sqrt bubble radius (area ∝ value), clamped for hover targets.
  function makeRadius(maxV, maxR) {
    const MIN_R = 5;
    return v => (!v || v <= 0) ? 0
      : Math.max(MIN_R, maxR * Math.sqrt(v / maxV));
  }

  function regionTooltip(title, lines) {
    return '<div class="gc-tip"><strong>' + title + '</strong>' +
      lines.map(l => '<br>' + l).join('') + '</div>';
  }

  // Base polygon layer; `valueOf(nuts3) -> number|0` decides the fill.
  function addRegions(map, geo, colorOf, tipOf) {
    const layer = L.geoJSON(geo, {
      pane: 'regions',
      style: f => ({
        weight: 0.6,
        color: COLORS.regionStroke,
        fillColor: colorOf(f.properties.NUTS_ID),
        fillOpacity: 0.95,
      }),
      onEachFeature: (f, lyr) => {
        const tip = tipOf && tipOf(f.properties.NUTS_ID, f.properties.NUTS_NAME);
        if (tip) lyr.bindTooltip(tip, { sticky: true, direction: 'top', className: 'gc-tt' });
        lyr.on({
          mouseover: e => e.target.setStyle({ weight: 1.6, color: COLORS.regionStrokeHover }),
          mouseout:  e => layer.resetStyle(e.target),
        });
      },
    }).addTo(map);
    return layer;
  }

  return { fmtEur, fmtEurShort, fmtInt,
           RAMP_WORKS, RAMP_HOME, COLORS,
           initPaperMap, makeChoro, makeRadius, regionTooltip, addRegions };
})();
