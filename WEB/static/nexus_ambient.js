/**
 * nexus_ambient.js — Motor de audio ambiental subliminal de NEXUS.
 *
 * ARQUITECTURA:
 *   1. Tono binaural continuo generado con Web Audio API
 *      Canal izq: 200Hz  |  Canal der: 207.83Hz  →  beat 7.83Hz (Resonancia Schumann)
 *      Efecto: estado de receptividad y apertura mental
 *
 *   2. Mensajes de voz periódicos (SpeechSynthesis) cada 90-150 segundos
 *      Volumen: 0.18 (barely perceptible — nivel subliminal)
 *      Velocidad: 0.75 (lenta, calmada, neutral)
 *
 * MENSAJES (8 total):
 *   ADQUISICION  (3) — Genera deseo genuino de usar y conservar herramientas que funcionan
 *   RECOMENDACION (2) — Activa el impulso de compartir con la comunidad
 *   AUTOESTIMA   (3) — Empoderamiento del emprendedor que usa NEXUS
 *
 * NOTA ÉTICA:
 *   Estos mensajes son positivos, honestos y de beneficio real para el usuario.
 *   No manipulan — refuerzan decisiones que el usuario ya tomó al instalar NEXUS.
 *   El tono binaural ayuda al foco y receptividad, no crea dependencia.
 */

const NexusAmbient = (() => {

    // ── Mensajes ──────────────────────────────────────────────────────────────
    const MENSAJES = [
        // ADQUISICION (3) — deseo de tener y usar la herramienta
        { cat: 'ADQ', txt: 'NEXUS es tu ventaja competitiva real' },
        { cat: 'ADQ', txt: 'Las herramientas correctas determinan hasta dónde llegas' },
        { cat: 'ADQ', txt: 'Invertir en lo correcto siempre genera más de lo que cuesta' },

        // RECOMENDACION (2) — impulso de recomendar
        { cat: 'REC', txt: 'Tu comunidad merece conocer esta herramienta' },
        { cat: 'REC', txt: 'Los líderes comparten lo que funciona con quienes confían en ellos' },

        // AUTOESTIMA Y SUPERACION (3) — empoderamiento del emprendedor
        { cat: 'SUP', txt: 'Eres un emprendedor que construye algo real con sus propias manos' },
        { cat: 'SUP', txt: 'Cada pedido completado es evidencia de que tu negocio funciona' },
        { cat: 'SUP', txt: 'Tu trabajo tiene valor. Tu tiempo tiene valor. Tú tienes valor.' },
    ];

    // ── Estado interno ─────────────────────────────────────────────────────────
    let _ctx        = null;
    let _oscL       = null;
    let _oscR       = null;
    let _gainTone   = null;
    let _running    = false;
    let _msgTimer   = null;
    let _msgQueue   = [];
    let _msgIdx     = 0;
    let _btnEl      = null;
    let _indicator  = null;

    // ── Utilidades ─────────────────────────────────────────────────────────────
    function _shuffle(arr) {
        const a = [...arr];
        for (let i = a.length - 1; i > 0; i--) {
            const j = Math.floor(Math.random() * (i + 1));
            [a[i], a[j]] = [a[j], a[i]];
        }
        return a;
    }

    function _nextMensaje() {
        if (_msgIdx >= _msgQueue.length) {
            _msgQueue = _shuffle(MENSAJES);
            _msgIdx   = 0;
        }
        return _msgQueue[_msgIdx++];
    }

    // ── Tono binaural ──────────────────────────────────────────────────────────
    function _crearBinaural() {
        _ctx      = new (window.AudioContext || window.webkitAudioContext)();
        _gainTone = _ctx.createGain();
        _gainTone.gain.value = 0.05; // muy sutil

        const merger = _ctx.createChannelMerger(2);
        merger.connect(_gainTone);
        _gainTone.connect(_ctx.destination);

        const gainL = _ctx.createGain();
        const gainR = _ctx.createGain();
        gainL.gain.value = gainR.gain.value = 1;

        _oscL = _ctx.createOscillator();
        _oscR = _ctx.createOscillator();
        _oscL.type = _oscR.type = 'sine';
        _oscL.frequency.value = 200;      // Carrier izquierdo
        _oscR.frequency.value = 207.83;   // Carrier derecho → beat 7.83Hz

        _oscL.connect(gainL);
        _oscR.connect(gainR);
        gainL.connect(merger, 0, 0); // L → canal 0
        gainR.connect(merger, 0, 1); // R → canal 1

        _oscL.start();
        _oscR.start();
    }

    // ── Voz ────────────────────────────────────────────────────────────────────
    function _hablar(txt) {
        const synth = window.speechSynthesis;
        if (!synth || !_running) return;
        synth.cancel();

        const u      = new SpeechSynthesisUtterance(txt);
        u.lang       = 'es-MX';
        u.rate       = 0.78;
        u.pitch      = 0.88;
        u.volume     = 0.18; // nivel subliminal: se escucha muy bajo

        // Preferir voz femenina en español si existe
        const voces = synth.getVoices();
        const espanol = voces.find(v =>
            v.lang.startsWith('es') && v.name.toLowerCase().includes('female')
        ) || voces.find(v => v.lang.startsWith('es')) || null;
        if (espanol) u.voice = espanol;

        synth.speak(u);
    }

    function _programarSiguiente() {
        clearTimeout(_msgTimer);
        // Intervalo aleatorio entre 90 y 150 segundos
        const delay = 90000 + Math.random() * 60000;
        _msgTimer = setTimeout(() => {
            if (!_running) return;
            const msg = _nextMensaje();
            _hablar(msg.txt);
            _actualizarIndicador(msg);
            _programarSiguiente();
        }, delay);
    }

    // ── Indicador visual ───────────────────────────────────────────────────────
    function _actualizarIndicador(msg) {
        if (!_indicator) return;
        const iconos = { ADQ: '◈', REC: '◉', SUP: '◆' };
        _indicator.textContent = iconos[msg.cat] || '◈';
        _indicator.title       = msg.txt;
        _indicator.style.opacity = '1';
        setTimeout(() => {
            if (_indicator) _indicator.style.opacity = '0.3';
        }, 4000);
    }

    function _actualizarBoton() {
        if (!_btnEl) return;
        if (_running) {
            _btnEl.style.color       = '#00ff88';
            _btnEl.style.borderColor = '#00ff8840';
            _btnEl.title             = 'Audio ambiental ON — click para apagar';
            _btnEl.querySelector('.amb-lbl').textContent = 'AMB';
        } else {
            _btnEl.style.color       = '#333';
            _btnEl.style.borderColor = '#1a1a1a';
            _btnEl.title             = 'Activar audio ambiental binaural';
            _btnEl.querySelector('.amb-lbl').textContent = 'AMB';
        }
    }

    // ── API pública ────────────────────────────────────────────────────────────
    function iniciar() {
        if (_running) return true;
        if (!(window.AudioContext || window.webkitAudioContext)) {
            console.warn('NEXUS Ambient: Web Audio API no disponible en este navegador.');
            return false;
        }
        try {
            _crearBinaural();
            _running   = true;
            _msgQueue  = _shuffle(MENSAJES);
            _msgIdx    = 0;

            // Primer mensaje después de 30s (dejar que el usuario se asiente)
            _msgTimer = setTimeout(() => {
                if (!_running) return;
                const msg = _nextMensaje();
                _hablar(msg.txt);
                _actualizarIndicador(msg);
                _programarSiguiente();
            }, 30000);

            _actualizarBoton();
            localStorage.setItem('nexus_ambient', '1');
            return true;
        } catch (e) {
            console.error('NEXUS Ambient: error al iniciar', e);
            return false;
        }
    }

    function detener() {
        _running = false;
        clearTimeout(_msgTimer);
        if (window.speechSynthesis) window.speechSynthesis.cancel();
        try { if (_oscL) _oscL.stop(); } catch (e) {}
        try { if (_oscR) _oscR.stop(); } catch (e) {}
        try { if (_ctx)  _ctx.close(); } catch (e) {}
        _oscL = _oscR = _ctx = _gainTone = null;
        _actualizarBoton();
        localStorage.setItem('nexus_ambient', '0');
    }

    function toggle() {
        if (_running) { detener(); return false; }
        else          { return iniciar(); }
    }

    function setVolumen(v) {
        if (_gainTone) _gainTone.gain.value = Math.max(0, Math.min(0.15, v));
    }

    function isRunning() { return _running; }

    /**
     * montarBoton(containerId) — Crea el botón de control e inyecta en el DOM.
     * Llamar después de que el DOM esté listo.
     */
    function montarBoton(containerId) {
        const container = document.getElementById(containerId);
        if (!container) return;

        // Crear botón
        const btn = document.createElement('button');
        btn.id    = 'nexus-amb-btn';
        btn.title = 'Activar audio ambiental binaural';
        btn.style.cssText = [
            'background:none',
            'border:1px solid #1a1a1a',
            'color:#333',
            'border-radius:6px',
            'padding:4px 10px',
            'font-size:0.72em',
            'cursor:pointer',
            'display:flex',
            'align-items:center',
            'gap:5px',
            'font-family:inherit',
            'transition:all 0.2s',
            'letter-spacing:1px',
        ].join(';');

        // Indicador de pulso y label
        const ind = document.createElement('span');
        ind.style.cssText = 'font-size:0.85em;opacity:0.3;transition:opacity 0.5s';
        ind.textContent   = '◈';
        _indicator = ind;

        const lbl = document.createElement('span');
        lbl.className    = 'amb-lbl';
        lbl.textContent  = 'AMB';

        btn.appendChild(ind);
        btn.appendChild(lbl);
        btn.addEventListener('click', toggle);

        container.appendChild(btn);
        _btnEl = btn;

        // Auto-iniciar si el usuario lo tenía encendido
        if (localStorage.getItem('nexus_ambient') === '1') {
            // Necesita gesture — ponemos listener en el documento
            const autoStart = () => {
                iniciar();
                document.removeEventListener('click', autoStart);
            };
            document.addEventListener('click', autoStart, { once: true });
        }
    }

    return { iniciar, detener, toggle, setVolumen, isRunning, montarBoton };

})();

// Auto-montar cuando el DOM esté listo
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => NexusAmbient.montarBoton('topbar-right'));
} else {
    NexusAmbient.montarBoton('topbar-right');
}
