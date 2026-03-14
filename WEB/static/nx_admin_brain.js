/**
 * nx_admin_brain.js — Cerebro completo para Admin
 * Conecta el PTT del admin con TODOS los módulos y acciones de NEXUS
 * Solo se activa en /admin — versión de Anuar
 */
(function(){ 'use strict';

// ── Mapa de navegación NEXUS completo ─────────────────────────────────────────
const NEXUS_URLS = {
  ver_pedidos:     '/pedidos',
  ver_clientes:    '/clientes',
  ver_stock:       '/stock',
  cotizar:         '/cotizar',
  historial:       '/historial',
  ver_finanzas:    '/finanzas',
  agenda:          '/agenda',
  marketing_panel: '/marketing/panel',
  galeria_atf:     '/atf/galeria',
  ver_agenda_atf:  '/atf',
  catalogo_atf:    '/canbusfix/catalogo',
  ver_pipeline:    '/autoventas',
  video_studio:    '/video-studio',
  cartoonizer:     '/cartoonizer',
  admin:           '/admin',
  ver_config:      '/config_negocio',
  resumen:         '/dashboard',
  merch_diseno:    '/merch-design',
  teens_panel:     '/teens',
  paranormal_modo: '/paranormal',
  marketing:       '/marketing/panel',
  setup:           '/setup',
  milens:          '/milens',
  canbusfix:       '/canbusfix',
};

// ── Paneles por palabra clave ─────────────────────────────────────────────────
const PANELES = [
  { keys:['pedido','orden','ordenes'],               url:'/pedidos' },
  { keys:['nuevo pedido','crear pedido'],            url:'/nuevo_pedido_form' },
  { keys:['cliente','clientes'],                     url:'/clientes' },
  { keys:['nuevo cliente','agregar cliente'],        url:'/nuevo_cliente_form' },
  { keys:['stock','inventario','material'],          url:'/stock' },
  { keys:['cotizar','cotizacion','presupuesto'],     url:'/cotizar' },
  { keys:['agenda','cita','agendar'],                url:'/agenda' },
  { keys:['marketing','caption','promo','publicar'], url:'/marketing/panel' },
  { keys:['autovent','pipeline','prospecto'],        url:'/autoventas' },
  { keys:['atf','faros','retrofit'],                 url:'/atf' },
  { keys:['canbusfix','canbus','instalador'],        url:'/canbusfix' },
  { keys:['milens','laser','corte'],                 url:'/milens' },
  { keys:['teens'],                                   url:'/teens' },
  { keys:['dashboard','inicio','panel principal'],   url:'/dashboard' },
  { keys:['estudio','studio'],                       url:'/estudio' },
  { keys:['cartoon','cartooniz'],                    url:'/cartoonizer' },
  { keys:['merch','playera','llavero'],               url:'/merch-design' },
  { keys:['video','videos'],                         url:'/video-studio' },
  { keys:['reporte','informe'],                      url:'/reporte' },
  { keys:['historial','log'],                        url:'/historial' },
  { keys:['tienda','catalogo','shop'],               url:'/tienda' },
  { keys:['mercado libre','meli'],                   url:'/mercado' },
  { keys:['config','configuracion'],                 url:'/config_negocio' },
  { keys:['precios','precio'],                       url:'/precios_admin' },
  { keys:['qr','codigo qr'],                         url:'/qr' },
  { keys:['paranormal'],                             url:'/paranormal' },
];

// ── Mostrar burbuja de respuesta ─────────────────────────────────────────────
function burbuja(txt, esIA) {
  let el = document.getElementById('_nx_brain_burbuja');
  if (!el) {
    el = document.createElement('div');
    el.id = '_nx_brain_burbuja';
    el.style.cssText = 'position:fixed;bottom:90px;left:50%;transform:translateX(-50%);' +
      'background:#0c1a10;border:1px solid #00ff8830;color:#c8e6d0;' +
      'padding:12px 18px;border-radius:14px;font-size:.85em;z-index:99990;' +
      'max-width:88vw;text-align:center;line-height:1.5;' +
      'box-shadow:0 4px 20px rgba(0,255,136,.1);transition:opacity .3s';
    document.body.appendChild(el);
  }
  el.style.opacity = '1';
  el.style.borderColor = esIA ? '#00cfff30' : '#00ff8830';
  el.style.color = esIA ? '#a0d8ef' : '#c8e6d0';
  el.textContent = txt;
  clearTimeout(el._t);
  el._t = setTimeout(() => { el.style.opacity = '0'; }, 4500);
}

// ── Hablar (usa la función global del admin panel si existe) ──────────────────
function hablar(txt) {
  if (window.hablar) { window.hablar(txt); return; }
  if (!window.speechSynthesis) return;
  speechSynthesis.cancel();
  const u = new SpeechSynthesisUtterance(txt);
  u.lang = 'es-MX'; u.rate = 1.0;
  const mx = speechSynthesis.getVoices().find(v => v.lang === 'es-MX') ||
             speechSynthesis.getVoices().find(v => v.lang.startsWith('es'));
  if (mx) u.voice = mx;
  speechSynthesis.speak(u);
}

// ── Ejecutar acción del cerebro ───────────────────────────────────────────────
async function ejecutar(accion, params) {
  if (!accion || accion === 'conversar' || accion === 'error') return;

  // Navegación directa
  if (accion === 'navegar' && params?.url) {
    setTimeout(() => window.location = params.url, 900); return;
  }
  if (NEXUS_URLS[accion]) {
    const url = NEXUS_URLS[accion];
    if (url.startsWith('/api/')) {
      const r = await fetch(url).then(x => x.json()).catch(() => ({}));
      burbuja(JSON.stringify(r).slice(0, 200), false);
    } else {
      setTimeout(() => window.location = url, 900);
    }
    return;
  }

  // Pedidos
  if (accion === 'crear_pedido') {
    if (params?.cliente && params?.producto) {
      const fd = new FormData();
      fd.append('cliente', params.cliente);
      fd.append('producto', params.producto);
      fd.append('entrega', params.deadline || '');
      fd.append('area', params.area || 'GENERAL');
      await fetch('/nuevo_pedido', { method: 'POST', body: fd }).catch(() => {});
      burbuja(`Pedido de ${params.cliente} registrado.`);
    } else { setTimeout(() => window.location = '/nuevo_pedido_form', 900); }
    return;
  }
  if (accion === 'nuevo_cliente') {
    if (params?.nombre) {
      const fd = new FormData();
      fd.append('nombre', params.nombre);
      fd.append('telefono', params.telefono || '');
      fd.append('email', params.email || '');
      await fetch('/nuevo_cliente', { method: 'POST', body: fd }).catch(() => {});
      burbuja(`Cliente ${params.nombre} registrado.`);
    } else { setTimeout(() => window.location = '/nuevo_cliente_form', 900); }
    return;
  }

  // Estudio / apps
  if (['abrir_corel','abrir_silhouette','abrir_aspire','abrir_app'].includes(accion)) {
    const appKey = params?.app || (accion === 'abrir_corel' ? 'corel' : accion === 'abrir_silhouette' ? 'silhouette' : 'aspire');
    const r = await fetch('/api/estudio/abrir', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ app: appKey, archivo: params?.archivo || null })
    }).then(x => x.json()).catch(() => ({ ok: false }));
    burbuja(r.ok ? `${appKey} abierto.` : `Error: ${r.error || 'sin respuesta'}`);
    return;
  }
  if (accion === 'ejecutar_macro') {
    const r = await fetch('/api/estudio/ejecutar_macro', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ macro: params?.macro || params?.nombre })
    }).then(x => x.json()).catch(() => ({ ok: false }));
    burbuja(r.ok ? 'Macro ejecutado.' : `Error: ${r.error}`);
    return;
  }
  if (accion === 'generar_caja') {
    const r = await fetch('/api/estudio/generar_caja', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(params)
    }).then(x => x.json()).catch(() => ({ ok: false }));
    if (r.ok && r.pdf) { burbuja('Caja generada.'); window.open(r.pdf, '_blank'); }
    else setTimeout(() => window.location = '/estudio', 900);
    return;
  }

  // Backup / sistema
  if (accion === 'backup') {
    const r = await fetch('/api/backup', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: '{}' })
      .then(x => x.json()).catch(() => ({}));
    burbuja(r.ok ? 'Backup completado.' : 'Backup iniciado.');
    return;
  }

  // MercadoLibre
  if (accion === 'meli_publicar_todo') {
    const r = await fetch('/api/meli/publicar_todo', { method: 'POST' }).then(x => x.json()).catch(() => ({}));
    burbuja(r.ok ? `${r.publicados} productos publicados.` : `ML: ${r.error || 'error'}`);
    return;
  }
  if (accion === 'meli_preguntas') {
    const r = await fetch('/api/meli/preguntas').then(x => x.json()).catch(() => ({}));
    burbuja(r.total ? `${r.total} preguntas sin responder.` : 'Sin preguntas pendientes.');
    return;
  }

  // Cotizar
  if (accion === 'cotizar') {
    const url = params?.tipo === 'rapido' ? '/cotizar-rapido' : '/cotizar';
    setTimeout(() => window.location = url, 900); return;
  }
}

// ── Función principal: procesar texto de voz en admin ─────────────────────────
async function procesarAdmin(texto) {
  const t = texto.toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '');

  // Navegación por keywords directa (sin IA, más rápido)
  for (const p of PANELES) {
    if (p.keys.some(k => t.includes(k))) {
      burbuja(`Abriendo ${p.url}...`);
      hablar(`Abriendo ${p.keys[0]}`);
      setTimeout(() => window.location = p.url, 800);
      return true;
    }
  }

  // Llamar al cerebro completo
  burbuja('Procesando...');
  try {
    const r = await fetch('/api/asistente', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ texto, session_id: 'admin' })
    });
    const d = await r.json();
    const resp = d.respuesta || '';
    if (resp) { burbuja(resp, true); hablar(resp.slice(0, 220)); }
    if (d.accion && d.accion !== 'conversar' && d.accion !== 'error') {
      await ejecutar(d.accion, d.params || {});
    }
    return true;
  } catch(e) {
    burbuja('Sin conexión con el cerebro.');
    return false;
  }
}

window.NxAdminBrain = { procesarAdmin, ejecutar, burbuja };

})();
