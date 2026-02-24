/**
 * nexus_galeria.js — Motor de experiencias visuales de NEXUS.
 *
 * Genera efectos visuales ambientales usando CSS + Canvas + SVG.
 * No requiere imágenes externas — todo generado en código.
 * La opacidad es baja (4-8%) para que sea sutil, no distractor.
 *
 * Experiencias disponibles:
 *   cosmos      — Partículas verdes (default NEXUS)
 *   aurea       — Espiral áurea de Fibonacci
 *   deep_space  — Campo estelar profundo
 *   bosque      — Gradiente de verdes naturales
 *   mandala     — Mandala generativo animado
 *   plasma      — Plasma naranja energético
 *   oceano      — Ondas de océano profundo
 *   flor_vida   — Flor de la Vida (geometría sagrada)
 */

const NexusGaleria = (() => {

    let _canvas  = null;
    let _ctx     = null;
    let _overlay = null;
    let _animId  = null;
    let _current = null;
    let _frame   = 0;

    // ── Setup del canvas overlay ──────────────────────────────────────────────
    function _crearOverlay() {
        if (_overlay) return;
        _overlay = document.createElement('div');
        _overlay.id = 'nexus-visual-overlay';
        _overlay.style.cssText = [
            'position:fixed', 'top:0', 'left:0', 'width:100vw', 'height:100vh',
            'pointer-events:none', 'z-index:0', 'opacity:0',
            'transition:opacity 1.5s ease',
        ].join(';');

        _canvas = document.createElement('canvas');
        _canvas.style.cssText = 'width:100%;height:100%;display:block';
        _overlay.appendChild(_canvas);
        document.body.insertBefore(_overlay, document.body.firstChild);
        document.body.style.position = 'relative';

        _resize();
        window.addEventListener('resize', _resize);
    }

    function _resize() {
        if (!_canvas) return;
        _canvas.width  = window.innerWidth;
        _canvas.height = window.innerHeight;
        _ctx = _canvas.getContext('2d');
    }

    // ── Experiencias visuales ─────────────────────────────────────────────────

    const EXPERIENCIAS = {

        // Partículas flotantes verdes — el alma de NEXUS
        cosmos(ctx, W, H, t) {
            ctx.clearRect(0, 0, W, H);
            const seed = 42;
            for (let i = 0; i < 80; i++) {
                const x  = ((Math.sin(i * 2.3 + seed) * 0.5 + 0.5) * W + t * (0.1 + i * 0.002)) % W;
                const y  = ((Math.cos(i * 1.7 + seed) * 0.5 + 0.5) * H + t * (0.05 + i * 0.001)) % H;
                const r  = 0.5 + Math.abs(Math.sin(i * 3.1 + t * 0.001)) * 1.5;
                const a  = 0.15 + Math.abs(Math.sin(i * 1.1 + t * 0.0008)) * 0.25;
                ctx.beginPath();
                ctx.arc(x, y, r, 0, Math.PI * 2);
                ctx.fillStyle = `rgba(0,255,136,${a})`;
                ctx.fill();
            }
        },

        // Espiral de Fibonacci
        aurea(ctx, W, H, t) {
            ctx.clearRect(0, 0, W, H);
            const cx = W / 2, cy = H / 2;
            const phi = 1.6180339887;
            ctx.strokeStyle = 'rgba(221,170,0,0.12)';
            ctx.lineWidth   = 1;
            ctx.beginPath();
            let angle = t * 0.0002;
            for (let i = 0; i < 400; i++) {
                const r  = 2 * Math.pow(phi, angle / (Math.PI * 2)) * (Math.min(W, H) / 600);
                const px = cx + r * Math.cos(angle);
                const py = cy + r * Math.sin(angle);
                i === 0 ? ctx.moveTo(px, py) : ctx.lineTo(px, py);
                angle += 0.05;
            }
            ctx.stroke();
            // Puntos en la espiral
            angle = t * 0.0002;
            for (let i = 0; i < 30; i++) {
                const r  = 2 * Math.pow(phi, angle / (Math.PI * 2)) * (Math.min(W, H) / 600);
                const px = cx + r * Math.cos(angle);
                const py = cy + r * Math.sin(angle);
                ctx.beginPath();
                ctx.arc(px, py, 1.5, 0, Math.PI * 2);
                ctx.fillStyle = `rgba(255,200,0,${0.1 + Math.sin(i + t * 0.001) * 0.08})`;
                ctx.fill();
                angle += Math.PI * 2 / 30;
            }
        },

        // Estrellas y nebulosa
        deep_space(ctx, W, H, t) {
            ctx.clearRect(0, 0, W, H);
            // Estrellas fijas
            for (let i = 0; i < 120; i++) {
                const x = (Math.sin(i * 137.5 * Math.PI / 180) * 0.5 + 0.5) * W;
                const y = (Math.cos(i * 137.5 * Math.PI / 180) * 0.5 + 0.5) * H;
                const a = 0.1 + Math.abs(Math.sin(i + t * 0.0005)) * 0.15;
                ctx.beginPath();
                ctx.arc(x, y, 0.8, 0, Math.PI * 2);
                ctx.fillStyle = `rgba(180,200,255,${a})`;
                ctx.fill();
            }
            // Nebulosa
            const grad = ctx.createRadialGradient(W * 0.3, H * 0.4, 0, W * 0.3, H * 0.4, W * 0.4);
            grad.addColorStop(0, `rgba(30,0,80,${0.08 + Math.sin(t * 0.0003) * 0.03})`);
            grad.addColorStop(1, 'rgba(0,0,0,0)');
            ctx.fillStyle = grad;
            ctx.fillRect(0, 0, W, H);
        },

        // Verde naturaleza
        bosque(ctx, W, H, t) {
            ctx.clearRect(0, 0, W, H);
            const grad = ctx.createLinearGradient(0, 0, W, H);
            const wave = Math.sin(t * 0.0004) * 0.03;
            grad.addColorStop(0,   `rgba(10,40,15,${0.18 + wave})`);
            grad.addColorStop(0.5, `rgba(20,60,25,${0.12 + wave})`);
            grad.addColorStop(1,   `rgba(5,30,10,${0.15 + wave})`);
            ctx.fillStyle = grad;
            ctx.fillRect(0, 0, W, H);
            // Líneas como rayos de luz entre hojas
            for (let i = 0; i < 8; i++) {
                const x = W * (i / 8) + Math.sin(t * 0.0002 + i) * 20;
                ctx.beginPath();
                ctx.moveTo(x, 0);
                ctx.lineTo(x + 30, H);
                ctx.strokeStyle = `rgba(100,200,80,${0.03 + Math.sin(t * 0.001 + i) * 0.015})`;
                ctx.lineWidth   = 15 + i * 3;
                ctx.stroke();
            }
        },

        // Mandala geométrico
        mandala(ctx, W, H, t) {
            ctx.clearRect(0, 0, W, H);
            const cx = W / 2, cy = H / 2;
            const R  = Math.min(W, H) * 0.35;
            const petals = 12;

            for (let p = 0; p < petals; p++) {
                const angle = (p / petals) * Math.PI * 2 + t * 0.0003;
                ctx.save();
                ctx.translate(cx, cy);
                ctx.rotate(angle);

                for (let ring = 1; ring <= 5; ring++) {
                    const r  = (ring / 5) * R;
                    const a  = 0.04 + Math.sin(t * 0.0005 + ring) * 0.02;
                    const hue = (p * 30 + ring * 15 + t * 0.01) % 360;
                    ctx.beginPath();
                    ctx.arc(0, r, r * 0.3, 0, Math.PI * 2);
                    ctx.strokeStyle = `hsla(${hue},60%,60%,${a})`;
                    ctx.lineWidth   = 1;
                    ctx.stroke();
                }
                ctx.restore();
            }
            // Círculo central
            ctx.beginPath();
            ctx.arc(cx, cy, R * 0.08, 0, Math.PI * 2);
            ctx.strokeStyle = `rgba(180,100,255,${0.06 + Math.sin(t * 0.001) * 0.03})`;
            ctx.lineWidth = 1;
            ctx.stroke();
        },

        // Plasma energético
        plasma(ctx, W, H, t) {
            ctx.clearRect(0, 0, W, H);
            for (let y = 0; y < H; y += 8) {
                for (let x = 0; x < W; x += 8) {
                    const v = Math.sin(x * 0.01 + t * 0.001)
                            + Math.sin(y * 0.01 + t * 0.0008)
                            + Math.sin((x + y) * 0.007 + t * 0.0006);
                    const r = Math.floor(200 + v * 30);
                    const g = Math.floor(60  + v * 20);
                    const b = Math.floor(0   + v * 10);
                    const a = 0.04 + Math.abs(v) * 0.02;
                    ctx.fillStyle = `rgba(${r},${g},${b},${a})`;
                    ctx.fillRect(x, y, 8, 8);
                }
            }
        },

        // Océano profundo
        oceano(ctx, W, H, t) {
            ctx.clearRect(0, 0, W, H);
            for (let i = 0; i < 6; i++) {
                const y    = H * 0.3 + i * H * 0.12 + Math.sin(t * 0.0003 + i * 0.8) * 20;
                const grad = ctx.createLinearGradient(0, y, 0, y + 80);
                const a    = 0.06 - i * 0.008;
                grad.addColorStop(0, `rgba(0,60,120,${a})`);
                grad.addColorStop(1, 'rgba(0,0,0,0)');
                ctx.fillStyle = grad;
                ctx.beginPath();
                ctx.moveTo(0, y);
                for (let x = 0; x <= W; x += 10) {
                    ctx.lineTo(x, y + Math.sin(x * 0.008 + t * 0.0004 + i) * 15);
                }
                ctx.lineTo(W, H);
                ctx.lineTo(0, H);
                ctx.closePath();
                ctx.fill();
            }
        },

        // Flor de la Vida
        flor_vida(ctx, W, H, t) {
            ctx.clearRect(0, 0, W, H);
            const cx  = W / 2, cy = H / 2;
            const r   = Math.min(W, H) * 0.08;
            const rot = t * 0.0001;
            const positions = [[0, 0]];
            for (let i = 0; i < 6; i++) {
                const a = i * Math.PI / 3 + rot;
                positions.push([Math.cos(a) * r, Math.sin(a) * r]);
            }
            for (let ring = 0; ring < 2; ring++) {
                for (let i = 0; i < 6; i++) {
                    const a = i * Math.PI / 3 + Math.PI / 6 + rot;
                    positions.push([Math.cos(a) * r * 2, Math.sin(a) * r * 2]);
                }
            }
            positions.forEach(([dx, dy]) => {
                const hue = (dx + dy + t * 0.02) % 360;
                const a   = 0.06 + Math.sin(t * 0.0004 + dx * 0.01) * 0.025;
                ctx.beginPath();
                ctx.arc(cx + dx, cy + dy, r, 0, Math.PI * 2);
                ctx.strokeStyle = `hsla(${hue},50%,70%,${a})`;
                ctx.lineWidth   = 1;
                ctx.stroke();
            });
        },
    };

    // ── Loop de animación ─────────────────────────────────────────────────────
    function _loop() {
        if (!_current || !_ctx) return;
        const fn = EXPERIENCIAS[_current];
        if (fn) fn(_ctx, _canvas.width, _canvas.height, _frame);
        _frame  += 1;
        _animId  = requestAnimationFrame(_loop);
    }

    // ── API pública ───────────────────────────────────────────────────────────
    function activar(css_key, opacidad = 0.06) {
        _crearOverlay();
        if (_animId) cancelAnimationFrame(_animId);
        _frame   = 0;
        _current = css_key;
        _overlay.style.opacity = String(opacidad);
        _loop();
        localStorage.setItem('nexus_visual', css_key);
        localStorage.setItem('nexus_visual_op', String(opacidad));
    }

    function desactivar() {
        if (_animId) cancelAnimationFrame(_animId);
        _animId  = null;
        _current = null;
        if (_overlay) _overlay.style.opacity = '0';
        localStorage.removeItem('nexus_visual');
    }

    function toggle(css_key) {
        if (_current === css_key) { desactivar(); return false; }
        activar(css_key);
        return true;
    }

    function setOpacidad(v) {
        if (_overlay) _overlay.style.opacity = String(Math.max(0.01, Math.min(0.15, v)));
    }

    function actual() { return _current; }

    // Auto-restaurar
    (function restore() {
        const k = localStorage.getItem('nexus_visual');
        const o = parseFloat(localStorage.getItem('nexus_visual_op') || '0.06');
        if (k) {
            if (document.readyState === 'loading') {
                document.addEventListener('DOMContentLoaded', () => activar(k, o));
            } else {
                activar(k, o);
            }
        }
    })();

    return { activar, desactivar, toggle, setOpacidad, actual, EXPERIENCIAS };

})();
