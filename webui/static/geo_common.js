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
    const o = opts || {};
    // locked: no user zoom/pan at all — the view only moves
    // programmatically (fitBounds on region drill-down).
    const lockedOpts = o.locked ? {
      zoomControl: false, dragging: false, doubleClickZoom: false,
      touchZoom: false, boxZoom: false, keyboard: false,
    } : {};
    const map = L.map(elId, Object.assign({
      zoomSnap: 0.25,
      attributionControl: false,
      zoomControl: true,
      scrollWheelZoom: false,   // page scroll stays usable; zoom via buttons
    }, lockedOpts, o)).setView([38.6, 24.2], 6.25);
    map.createPane('regions'); map.getPane('regions').style.zIndex = 350;
    map.createPane('links');   map.getPane('links').style.zIndex = 420;
    map.createPane('bubbles'); map.getPane('bubbles').style.zIndex = 450;
    map.createPane('pins');    map.getPane('pins').style.zIndex = 500;
    if (!o.locked) {
      map.on('focus', () => map.scrollWheelZoom.enable());
      map.on('blur', () => map.scrollWheelZoom.disable());
    }
    return map;
  }

  // Fixed info box pinned to the map's lower-left corner — an alternative to
  // mouse-following tooltips. Returns {show(html), hide()}.
  function pinnedTip(map) {
    const el = document.createElement('div');
    el.className = 'gc-pin-tt';
    el.hidden = true;
    map.getContainer().appendChild(el);
    return {
      show(html) { el.innerHTML = html; el.hidden = false; },
      hide() { el.hidden = true; el.innerHTML = ''; },
    };
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

  // Region id + display name off a polygon feature. The Π.Ε. layer uses
  // {pe, name}; the retired NUTS-3 layer used {NUTS_ID, NUTS_NAME}.
  const regionId = f => f.properties.pe ?? f.properties.NUTS_ID;
  const regionName = f => f.properties.name ?? f.properties.NUTS_NAME;

  // Base polygon layer; `colorOf(regionId) -> css color` decides the fill.
  // Optional onClick(regionId, regionName) makes regions clickable
  // (drill-down). Optional tipSink (a pinnedTip) shows the tooltip in the
  // map corner instead of a mouse-following one.
  function addRegions(map, geo, colorOf, tipOf, onClick, tipSink) {
    const layer = L.geoJSON(geo, {
      pane: 'regions',
      style: f => ({
        weight: 0.6,
        color: COLORS.regionStroke,
        fillColor: colorOf(regionId(f)),
        fillOpacity: 0.95,
      }),
      onEachFeature: (f, lyr) => {
        const tip = tipOf && tipOf(regionId(f), regionName(f));
        if (tip && !tipSink)
          lyr.bindTooltip(tip, { sticky: true, direction: 'top', className: 'gc-tt' });
        lyr.on({
          mouseover: e => {
            e.target.setStyle({ weight: 1.6, color: COLORS.regionStrokeHover });
            if (onClick) map.getContainer().style.cursor = 'pointer';
            if (tip && tipSink) tipSink.show(tip);
          },
          mouseout: e => {
            layer.resetStyle(e.target);
            if (onClick) map.getContainer().style.cursor = '';
            if (tipSink) tipSink.hide();
          },
        });
        if (onClick) lyr.on('click', () =>
          onClick(regionId(f), regionName(f)));
      },
    }).addTo(map);
    return layer;
  }

  // Deterministic de-overlap: points sharing (rounded) coordinates are laid
  // out on a small sunflower spiral around the shared spot so every dot
  // stays visible ("move them around a little"). No randomness — stable
  // across renders. Returns new objects with adjusted lat/lon.
  function spreadOverlaps(points, stepDeg) {
    const step = stepDeg || 0.028;               // ~2.5 km at Greek latitudes
    const groups = new Map();
    points.forEach(p => {
      const key = p.lat.toFixed(3) + ',' + p.lon.toFixed(3);
      if (!groups.has(key)) groups.set(key, []);
      groups.get(key).push(p);
    });
    const out = [];
    const GOLDEN = Math.PI * (3 - Math.sqrt(5));
    groups.forEach(members => {
      if (members.length === 1) { out.push(members[0]); return; }
      members.forEach((p, i) => {
        if (i === 0) { out.push(p); return; }    // first stays put
        const r = step * Math.sqrt(i);
        const a = i * GOLDEN;
        out.push(Object.assign({}, p, {
          lat: p.lat + r * Math.sin(a),
          lon: p.lon + r * Math.cos(a) / Math.cos(p.lat * Math.PI / 180),
        }));
      });
    });
    return out;
  }

  // Equal-size dot layer (presence, not magnitude). opts: {fill, stroke,
  // radius, tipOf(p) -> html, hrefOf(p) -> url|null, fillOf(p) -> css color
  // (per-dot override of fill), tipSink (corner box instead of tooltip),
  // onOver(p)/onOut(p) (extra hover hooks, e.g. sibling-link lines)}.
  function addDots(map, points, opts) {
    const o = Object.assign({ radius: 5, fillOpacity: 0.78, weight: 1 }, opts || {});
    const layer = L.layerGroup(points.map(p => {
      const m = L.circleMarker([p.lat, p.lon], {
        pane: 'bubbles', radius: o.radius,
        fillColor: o.fillOf ? o.fillOf(p) : o.fill, fillOpacity: o.fillOpacity,
        color: o.stroke, weight: o.weight,
      });
      if (o.onOver) m.on('mouseover', () => o.onOver(p));
      if (o.onOut) m.on('mouseout', () => o.onOut(p));
      if (o.tipOf && o.tipSink) {
        m.on('mouseover', () => o.tipSink.show(o.tipOf(p)));
        m.on('mouseout', () => o.tipSink.hide());
      } else if (o.tipOf) {
        m.bindTooltip(o.tipOf(p),
          { sticky: true, direction: 'top', className: 'gc-tt' });
      }
      if (o.hrefOf) {
        const href = o.hrefOf(p);
        if (href) {
          m.on('click', () => { window.location = href; });
          m.on('mouseover', () => { map.getContainer().style.cursor = 'pointer'; });
          m.on('mouseout', () => { map.getContainer().style.cursor = ''; });
        }
      }
      return m;
    })).addTo(map);
    return layer;
  }

  return { fmtEur, fmtEurShort, fmtInt,
           RAMP_WORKS, RAMP_HOME, COLORS,
           initPaperMap, makeChoro, makeRadius, regionTooltip, addRegions,
           spreadOverlaps, addDots, pinnedTip, regionId, regionName };
})();
