/**
 * nx_security.js — NEXUS Security Layer
 * Protege todas las versiones contra copia, clonado e inspección
 * Solo admin puede operar el sistema completo
 */
(function () { 'use strict';

  // ── 1. Bloquear menú contextual (botón derecho) ─────────────────────────────
  document.addEventListener('contextmenu', function (e) { e.preventDefault(); });

  // ── 2. Bloquear teclas de inspección y copiado ──────────────────────────────
  document.addEventListener('keydown', function (e) {
    const k = e.key;
    const ctrl = e.ctrlKey || e.metaKey;
    const shift = e.shiftKey;

    // F12 — DevTools
    if (k === 'F12') { e.preventDefault(); _registrarViolacion(); return; }

    // Ctrl+Shift+I / J / C — DevTools
    if (ctrl && shift && (k === 'I' || k === 'i' || k === 'J' || k === 'j' || k === 'C' || k === 'c')) {
      e.preventDefault(); _registrarViolacion(); return;
    }

    // Ctrl+U — Ver fuente
    if (ctrl && (k === 'U' || k === 'u')) { e.preventDefault(); _registrarViolacion(); return; }

    // Ctrl+S — Guardar página
    if (ctrl && (k === 'S' || k === 's')) { e.preventDefault(); return; }

    // Ctrl+A — Seleccionar todo (excepto en inputs y textareas)
    if (ctrl && (k === 'A' || k === 'a')) {
      const tag = (e.target.tagName || '').toLowerCase();
      if (tag !== 'input' && tag !== 'textarea') { e.preventDefault(); return; }
    }

    // Ctrl+P — Imprimir
    if (ctrl && (k === 'P' || k === 'p')) { e.preventDefault(); return; }
  });

  // ── 3. Bloquear selección de texto fuera de inputs ──────────────────────────
  document.addEventListener('selectstart', function (e) {
    const tag = (e.target.tagName || '').toLowerCase();
    if (tag !== 'input' && tag !== 'textarea') e.preventDefault();
  });

  // ── 4. Bloquear arrastrar elementos ─────────────────────────────────────────
  document.addEventListener('dragstart', function (e) { e.preventDefault(); });

  // ── 5. Bloquear impresión ────────────────────────────────────────────────────
  window.addEventListener('beforeprint', function (e) { e.preventDefault(); window.print = function(){}; });

  // ── 6. Detectar DevTools + bloqueo permanente por violaciones ────────────────
  const _LOCK_KEY = '_nx_bloqueado';
  const _ATTEMPTS_KEY = '_nx_attempts';

  // Si ya fue bloqueado permanentemente → pantalla de bloqueo inmediata
  if (localStorage.getItem(_LOCK_KEY) === '1') {
    document.addEventListener('DOMContentLoaded', _bloqueoDefinitivo);
  }

  function _registrarViolacion() {
    const n = parseInt(localStorage.getItem(_ATTEMPTS_KEY) || '0') + 1;
    localStorage.setItem(_ATTEMPTS_KEY, n);
    if (n >= 3) {
      // 3 intentos → bloqueo permanente
      localStorage.setItem(_LOCK_KEY, '1');
      _bloqueoDefinitivo();
    } else {
      _mostrarBloqueo();
    }
  }

  function _bloqueoDefinitivo() {
    document.body.innerHTML = '';
    document.head.innerHTML = '';
    const d = document.createElement('div');
    d.style.cssText = 'position:fixed;inset:0;background:#000;display:flex;flex-direction:column;' +
      'align-items:center;justify-content:center;font-family:monospace;text-align:center;gap:16px;padding:24px';
    d.innerHTML = `
      <div style="font-size:2.5em;font-weight:900;color:#ff2222;letter-spacing:6px">BLOQUEADO</div>
      <div style="font-size:.9em;color:#ff4444;max-width:280px;line-height:1.7">
        Acceso denegado permanentemente.<br>
        Este dispositivo ha sido bloqueado por violar los términos de uso de NEXUS by Simplex.
      </div>
      <div style="font-size:.7em;color:#2a1a1a;margin-top:16px">
        © NEXUS by Simplex — ID: ${_fingerprint()}
      </div>`;
    document.documentElement.appendChild(d);
    // Evitar navegación
    window.onbeforeunload = () => '';
    history.pushState(null, '', location.href);
    window.addEventListener('popstate', () => history.pushState(null, '', location.href));
  }

  function _fingerprint() {
    return btoa(navigator.userAgent + screen.width + screen.height).slice(0, 16);
  }

  let _devToolsAbierto = false;
  const _checkDevTools = function () {
    const umbral = 160;
    const abierto = (window.outerWidth - window.innerWidth > umbral) ||
                    (window.outerHeight - window.innerHeight > umbral);
    if (abierto && !_devToolsAbierto) {
      _devToolsAbierto = true;
      _registrarViolacion();
    } else if (!abierto && _devToolsAbierto) {
      _devToolsAbierto = false;
    }
  };
  setInterval(_checkDevTools, 1500);

  // ── 7. Bloquear iframe embedding ────────────────────────────────────────────
  if (window.self !== window.top) {
    // Redirigir al top si alguien intentó embeber en iframe
    try { window.top.location.href = window.self.location.href; } catch(e) {}
    document.body.innerHTML = '';
  }

  // ── Aviso breve ──────────────────────────────────────────────────────────────
  function _aviso() {
    let el = document.getElementById('_nx_sec_toast');
    if (!el) {
      el = document.createElement('div');
      el.id = '_nx_sec_toast';
      el.style.cssText = 'position:fixed;top:16px;left:50%;transform:translateX(-50%);' +
        'background:#1a0808;color:#ff6666;border:1px solid #ff444440;' +
        'padding:10px 20px;border-radius:10px;font-size:13px;z-index:999999;' +
        'pointer-events:none;font-family:monospace;letter-spacing:.5px';
      document.body.appendChild(el);
    }
    el.textContent = '⚠ NEXUS — Acceso restringido';
    el.style.opacity = '1';
    clearTimeout(el._t);
    el._t = setTimeout(() => { el.style.opacity = '0'; }, 2000);
  }

  // ── Pantalla de bloqueo al abrir DevTools ────────────────────────────────────
  function _mostrarBloqueo() {
    if (document.getElementById('_nx_devtools_block')) return;
    const d = document.createElement('div');
    d.id = '_nx_devtools_block';
    d.style.cssText = 'position:fixed;inset:0;background:#000;z-index:9999999;' +
      'display:flex;flex-direction:column;align-items:center;justify-content:center;' +
      'color:#00ff88;font-family:monospace;text-align:center;gap:12px';
    d.innerHTML = `
      <div style="font-size:2em;font-weight:900;letter-spacing:4px">NEXUS</div>
      <div style="font-size:1em;color:#ff4444">Acceso de desarrollador detectado</div>
      <div style="font-size:.75em;color:#4a6a55;max-width:280px;line-height:1.6">
        Este sistema es propiedad exclusiva de Simplex.<br>
        No está permitido copiar, clonar ni modificar.
      </div>
      <div style="font-size:.65em;color:#2a3a2a;margin-top:8px">
        © NEXUS by Simplex — Todos los derechos reservados
      </div>`;
    document.body.appendChild(d);
  }

  // ── Marca de agua invisible en consola ───────────────────────────────────────
  setTimeout(() => {
    console.clear();
    console.log('%c⚠ NEXUS by Simplex', 'color:#ff4444;font-size:20px;font-weight:bold');
    console.log('%cEste sistema es de uso exclusivo de Simplex GDL.\nNo está permitido copiar, clonar ni distribuir.\n© 2024 Simplex — Todos los derechos reservados.',
      'color:#888;font-size:13px');
  }, 800);

})();
