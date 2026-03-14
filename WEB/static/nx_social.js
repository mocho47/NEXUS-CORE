/**
 * nx_social.js — NEXUS Social Navigator
 * Abre apps sociales por voz + genera respuestas IA para WhatsApp/Messenger
 * Funciona en teens, admin y bienvenida_beta
 */
(function(){ 'use strict';

// ── Mapa de sitios ─────────────────────────────────────────────────────────────
const SITIOS = {
  'whatsapp':   'https://web.whatsapp.com',
  'messenger':  'https://www.messenger.com',
  'facebook':   'https://www.facebook.com',
  'instagram':  'https://www.instagram.com',
  'tiktok':     'https://www.tiktok.com',
  'youtube':    'https://www.youtube.com',
  'twitter':    'https://twitter.com',
  'x':          'https://x.com',
  'google':     'https://www.google.com',
  'gmail':      'https://mail.google.com',
  'spotify':    'https://open.spotify.com',
  'maps':       'https://maps.google.com',
};

// Alias de voz → clave en SITIOS
const ALIAS = [
  { keys:['whatsapp','wats','wasap','chat'],       site:'whatsapp' },
  { keys:['messenger','messen','mensajes facebook','chat de face'], site:'messenger' },
  { keys:['facebook','face','fb'],                  site:'facebook' },
  { keys:['instagram','insta','ig'],                site:'instagram' },
  { keys:['tiktok','tik tok','tik'],                site:'tiktok' },
  { keys:['youtube','you tube','yt','videos'],       site:'youtube' },
  { keys:['twitter','twiter'],                      site:'twitter' },
  { keys:['google','busca','buscador'],              site:'google' },
  { keys:['gmail','correo','email','mail'],          site:'gmail' },
  { keys:['spotify','musica','música'],              site:'spotify' },
  { keys:['maps','mapa','ubicacion','ubicación'],   site:'maps' },
];

// ── Abre URL en nueva pestaña ──────────────────────────────────────────────────
function abrirSitio(site, extra) {
  const url = extra || SITIOS[site];
  if (url) window.open(url, '_blank');
}

// ── Generador de respuesta con IA ─────────────────────────────────────────────
async function generarRespuestaIA(mensaje, app) {
  try {
    const res = await fetch('/api/asistente/beta', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        texto: `Genera una respuesta corta, natural y amable para este mensaje de ${app}: "${mensaje}". Solo dame el texto de la respuesta, sin comillas, sin explicación.`,
        session_id: 'social'
      })
    });
    const d = await res.json();
    return d.respuesta || d.reply || '';
  } catch(e) {
    return '';
  }
}

// ── Copia al portapapeles ──────────────────────────────────────────────────────
function copiarClipboard(txt) {
  if (navigator.clipboard) {
    navigator.clipboard.writeText(txt).catch(()=>{});
  } else {
    const ta = document.createElement('textarea');
    ta.value = txt; ta.style.position='fixed'; ta.style.opacity='0';
    document.body.appendChild(ta); ta.select();
    document.execCommand('copy');
    document.body.removeChild(ta);
  }
}

// ── Toast de notificación ──────────────────────────────────────────────────────
function toast(msg, color) {
  let el = document.getElementById('_nx_social_toast');
  if (!el) {
    el = document.createElement('div');
    el.id = '_nx_social_toast';
    el.style.cssText = 'position:fixed;bottom:90px;left:50%;transform:translateX(-50%);' +
      'background:#1a2e20;color:#00ff88;padding:10px 20px;border-radius:20px;' +
      'font-size:13px;z-index:99999;pointer-events:none;transition:opacity .3s;' +
      'border:1px solid #00ff8840;max-width:90vw;text-align:center;white-space:pre-line';
    document.body.appendChild(el);
  }
  el.style.color = color || '#00ff88';
  el.style.opacity = '1';
  el.textContent = msg;
  clearTimeout(el._t);
  el._t = setTimeout(() => { el.style.opacity = '0'; }, 3500);
}

// ── Modal de contestar ─────────────────────────────────────────────────────────
function mostrarModalContestacion(app, mensajeRecibido, respuestaIA) {
  let modal = document.getElementById('_nx_reply_modal');
  if (!modal) {
    modal = document.createElement('div');
    modal.id = '_nx_reply_modal';
    modal.style.cssText = 'position:fixed;inset:0;background:rgba(0,0,0,.88);z-index:99998;' +
      'display:flex;align-items:flex-end;justify-content:center;padding:16px';
    document.body.appendChild(modal);
  }
  modal.innerHTML = `
    <div style="background:#0c1a10;border:1px solid #1a3020;border-radius:16px;
      padding:20px;width:100%;max-width:480px;max-height:80vh;overflow-y:auto">
      <div style="font-size:.7em;color:#4a6a55;text-transform:uppercase;letter-spacing:1px;margin-bottom:4px">
        Respuesta sugerida — ${app}
      </div>
      <div style="font-size:.8em;color:#4a6a55;margin-bottom:12px;padding:8px;background:#060e0a;border-radius:8px;border-left:2px solid #1a3020">
        📩 "${mensajeRecibido}"
      </div>
      <textarea id="_nx_reply_txt" style="width:100%;background:#060e0a;border:1px solid #1a3020;
        border-radius:8px;padding:10px;color:#c8e6d0;font-size:.95em;resize:none;
        font-family:inherit;outline:none;min-height:80px" rows="4">${respuestaIA}</textarea>
      <div style="display:flex;gap:8px;margin-top:10px">
        <button onclick="_nxSocialCopiarYAbrir('${app}')"
          style="flex:1;padding:12px;background:#00ff8815;border:1px solid #00ff8840;
          color:#00ff88;border-radius:8px;cursor:pointer;font-size:.85em;font-weight:700">
          📋 Copiar y abrir ${app}
        </button>
        <button onclick="document.getElementById('_nx_reply_modal').style.display='none'"
          style="padding:12px 16px;background:#1a0a0a;border:1px solid #3a1a1a;
          color:#ff6666;border-radius:8px;cursor:pointer;font-size:.85em">
          ✕
        </button>
      </div>
    </div>`;
  modal.style.display = 'flex';

  window._nxSocialCopiarYAbrir = function(appName) {
    const txt = document.getElementById('_nx_reply_txt').value;
    copiarClipboard(txt);
    modal.style.display = 'none';
    const site = appName.toLowerCase().includes('messenger') ? 'messenger' : 'whatsapp';
    setTimeout(() => abrirSitio(site), 300);
    toast('✓ Copiado — pega en ' + appName, '#00cfff');
    if (window.NX?.hablar) NX.hablar('Respuesta copiada. Abriendo ' + appName);
    else if (window.hablar) hablar('Respuesta copiada. Abriendo ' + appName);
  };
}

// ── Estado para flujo de "contestar" ──────────────────────────────────────────
let _contestarApp = null;  // 'WhatsApp' | 'Messenger'

// ── Función principal: procesar texto de voz ──────────────────────────────────
async function procesarSocial(texto) {
  const t = texto.toLowerCase()
    .normalize('NFD').replace(/[\u0300-\u036f]/g, '');

  // Si estamos esperando el mensaje a contestar
  if (_contestarApp) {
    const app = _contestarApp;
    _contestarApp = null;
    toast('Generando respuesta para ' + app + '...', '#00cfff');
    const resp = await generarRespuestaIA(texto, app);
    if (resp) {
      mostrarModalContestacion(app, texto, resp);
    } else {
      toast('No pude generar respuesta. Intenta de nuevo.', '#ff6666');
    }
    return true;
  }

  // "contesta / responde + app"
  const esContestar = /contesta|responde|reply/.test(t);
  if (esContestar) {
    let app = 'WhatsApp';
    if (/messenger|messen|face/.test(t)) app = 'Messenger';
    _contestarApp = app;
    const msg = 'Dime el mensaje que quieres contestar de ' + app;
    toast('🎙️ ' + msg);
    if (window.NX?.hablar) NX.hablar(msg);
    else if (window.hablar) hablar(msg);
    return true;
  }

  // "busca X en youtube/google"
  let m = t.match(/busca(?:r)?\s+(.+?)\s+en\s+(youtube|google|you\s*tube)/);
  if (m) {
    const q = encodeURIComponent(m[1]);
    const url = /youtube/.test(m[2])
      ? `https://youtube.com/results?search_query=${q}`
      : `https://google.com/search?q=${q}`;
    window.open(url, '_blank');
    toast('Buscando "' + m[1] + '"');
    return true;
  }

  // "abre / entra a / ve a + sitio"
  m = t.match(/(?:abre?|entra\s+a|ve\s+a|p[aá]gina\s+de|ir\s+a|abrir)\s+(.+)/);
  if (m) {
    const query = m[1].trim();
    for (const a of ALIAS) {
      if (a.keys.some(k => query.includes(k))) {
        abrirSitio(a.site);
        toast('Abriendo ' + a.site.charAt(0).toUpperCase() + a.site.slice(1));
        if (window.NX?.hablar) NX.hablar('Abriendo ' + a.site);
        else if (window.hablar) hablar('Abriendo ' + a.site);
        return true;
      }
    }
  }

  // Solo mencionan el sitio directamente
  for (const a of ALIAS) {
    if (a.keys.some(k => t.includes(k))) {
      // Solo si el texto es corto (< 5 palabras) para evitar falsos positivos
      if (texto.trim().split(' ').length <= 4) {
        abrirSitio(a.site);
        toast('Abriendo ' + a.site.charAt(0).toUpperCase() + a.site.slice(1));
        if (window.NX?.hablar) NX.hablar('Abriendo ' + a.site);
        else if (window.hablar) hablar('Abriendo ' + a.site);
        return true;
      }
    }
  }

  return false; // No fue un comando social
}

// Exponer globalmente
window.NxSocial = { procesarSocial, abrirSitio, SITIOS, toast };

})();
