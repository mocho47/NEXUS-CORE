// NEXUS PTT — Push to Talk universal
// Uso: NxPTT.init({ onResult: fn, lang: 'es-MX' })
(function(w){
  const NxPTT = {
    _rec: null,
    _btn: null,
    _lbl: null,
    _active: false,
    _opts: {},

    init(opts = {}) {
      const Rec = w.SpeechRecognition || w.webkitSpeechRecognition;
      if (!Rec) {
        console.warn('NxPTT: SpeechRecognition no disponible en este navegador');
        this._crearBotonFallback();
        return;
      }
      this._opts = opts;

      // Crear botón flotante PTT
      const btn = document.createElement('div');
      btn.id = 'nx-ptt-btn';
      btn.innerHTML = '🎙️';
      btn.style.cssText = `
        position:fixed; bottom:calc(20px + env(safe-area-inset-bottom,0px)); right:20px;
        width:62px; height:62px; border-radius:50%;
        background:linear-gradient(135deg,#003020,#005030);
        border:2px solid #00ff88;
        display:flex; align-items:center; justify-content:center;
        font-size:1.6em; cursor:pointer; z-index:9990;
        box-shadow:0 4px 20px #00ff8833;
        transition:all .15s; user-select:none; -webkit-user-select:none;
        touch-action:none;
      `;

      const lbl = document.createElement('div');
      lbl.id = 'nx-ptt-lbl';
      lbl.textContent = 'Mantén';
      lbl.style.cssText = `
        position:fixed; bottom:calc(86px + env(safe-area-inset-bottom,0px)); right:6px;
        font-size:.6em; color:#4a6a55; text-align:center; width:74px; z-index:9990;
        font-family:-apple-system,sans-serif; letter-spacing:.5px; pointer-events:none;
      `;

      document.body.appendChild(btn);
      document.body.appendChild(lbl);
      this._btn = btn;
      this._lbl = lbl;

      const start = (e) => {
        e.preventDefault();
        e.stopPropagation();
        if (this._active) return;
        this._active = true;
        this._setEstado('escuchando');
        this._iniciarRec();
      };

      const stop = (e) => {
        e.preventDefault();
        if (!this._active) return;
        this._active = false;
        this._setEstado('normal');
        if (this._rec) {
          try { this._rec.stop(); } catch(_) {}
          this._rec = null;
        }
      };

      btn.addEventListener('touchstart', start, { passive: false });
      btn.addEventListener('touchend',   stop,  { passive: false });
      btn.addEventListener('touchcancel',stop,  { passive: false });
      btn.addEventListener('mousedown',  start);
      btn.addEventListener('mouseup',    stop);
      btn.addEventListener('mouseleave', stop);

      // Liberar mic al ocultar página o entrar llamada
      document.addEventListener('visibilitychange', () => {
        if (document.hidden) stop({ preventDefault(){} });
        if (document.hidden) w.speechSynthesis?.cancel();
      });
      w.addEventListener('freeze', () => stop({ preventDefault(){} }));
    },

    _iniciarRec() {
      const Rec = w.SpeechRecognition || w.webkitSpeechRecognition;
      if (!Rec || !this._active) return;

      const rec = new Rec();
      rec.lang           = this._opts.lang || 'es-MX';
      rec.continuous     = true;   // sigue escuchando mientras se mantiene el botón
      rec.interimResults = false;
      rec.maxAlternatives = 1;
      this._rec = rec;

      rec.onresult = (e) => {
        // Tomar el último resultado final
        for (let i = e.resultIndex; i < e.results.length; i++) {
          if (e.results[i].isFinal) {
            const txt = e.results[i][0].transcript.trim();
            if (txt && this._opts.onResult) this._opts.onResult(txt);
          }
        }
      };

      rec.onerror = (e) => {
        if (e.error === 'not-allowed' || e.error === 'permission-denied') {
          this._setEstado('error', '⚠ Sin permiso de mic');
          this._active = false;
          setTimeout(() => this._setEstado('normal'), 2500);
        } else if (e.error === 'no-speech') {
          // Normal — el usuario no habló; si sigue presionado, reiniciar
          if (this._active) {
            try { this._rec?.stop(); } catch(_) {}
            setTimeout(() => { if (this._active) this._iniciarRec(); }, 150);
          }
        } else if (e.error === 'network') {
          this._setEstado('error', '⚠ Sin red');
          this._active = false;
          setTimeout(() => this._setEstado('normal'), 2000);
        } else {
          // Otro error: intentar reiniciar si sigue activo
          if (this._active) {
            setTimeout(() => { if (this._active) this._iniciarRec(); }, 200);
          }
        }
      };

      rec.onend = () => {
        // Si el usuario aún mantiene el botón, reiniciar automáticamente
        if (this._active) {
          setTimeout(() => { if (this._active) this._iniciarRec(); }, 100);
        }
      };

      try {
        rec.start();
      } catch(err) {
        // Si ya hay una instancia corriendo, esperar y reintentar
        setTimeout(() => { if (this._active) this._iniciarRec(); }, 300);
      }
    },

    _setEstado(estado, mensaje) {
      const btn = this._btn;
      const lbl = this._lbl;
      if (!btn) return;
      if (estado === 'escuchando') {
        btn.style.background = 'linear-gradient(135deg,#001800,#00ff8855)';
        btn.style.boxShadow  = '0 0 28px #00ff8877';
        btn.style.border     = '2px solid #00ff88';
        btn.innerHTML = '🔴';
        if (lbl) { lbl.textContent = 'Escuchando'; lbl.style.color = '#00ff88'; }
      } else if (estado === 'error') {
        btn.style.background = 'linear-gradient(135deg,#200000,#ff444433)';
        btn.style.boxShadow  = '0 0 20px #ff444455';
        btn.innerHTML = '⚠️';
        if (lbl) { lbl.textContent = mensaje || 'Error'; lbl.style.color = '#ff6666'; }
      } else {
        btn.style.background = 'linear-gradient(135deg,#003020,#005030)';
        btn.style.boxShadow  = '0 4px 20px #00ff8833';
        btn.style.border     = '2px solid #00ff88';
        btn.innerHTML = '🎙️';
        if (lbl) { lbl.textContent = 'Mantén'; lbl.style.color = '#4a6a55'; }
      }
    },

    _crearBotonFallback() {
      // Navegador sin SpeechRecognition — botón que avisa
      const btn = document.createElement('div');
      btn.id = 'nx-ptt-btn';
      btn.innerHTML = '🎙️';
      btn.style.cssText = `
        position:fixed; bottom:calc(20px + env(safe-area-inset-bottom,0px)); right:20px;
        width:62px; height:62px; border-radius:50%;
        background:linear-gradient(135deg,#1a1a0a,#2a2a10);
        border:2px solid #888; display:flex; align-items:center; justify-content:center;
        font-size:1.6em; cursor:pointer; z-index:9990; opacity:.5;
      `;
      btn.title = 'Usa Chrome o Edge para voz';
      btn.onclick = () => alert('Para usar voz necesitas Chrome o Edge.');
      document.body.appendChild(btn);
    },

    hablar(txt, onEnd) {
      if (!w.speechSynthesis) { onEnd?.(); return; }
      speechSynthesis.cancel();
      const u = new SpeechSynthesisUtterance(txt);
      u.lang = 'es-MX'; u.rate = 1.05;
      const vs = speechSynthesis.getVoices();
      const mx = vs.find(v => v.lang === 'es-MX') || vs.find(v => v.lang.startsWith('es'));
      if (mx) u.voice = mx;
      if (onEnd) u.onend = onEnd;
      speechSynthesis.speak(u);
    }
  };

  w.NxPTT = NxPTT;
})(window);
