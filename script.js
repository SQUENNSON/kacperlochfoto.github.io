/* ============================================================
   sq_photo — GOD MODE Script
   ============================================================ */

'use strict';

/* ── CANVAS: Particle Network + Camera Viewfinder ──────────── */

class ParticleViewfinderCanvas {
    constructor(id) {
        this.canvas = document.getElementById(id);
        if (!this.canvas) return;
        this.ctx       = this.canvas.getContext('2d');
        this.mouse     = { x: -9999, y: -9999 };
        this.t         = 0;
        this.W = this.H = 0;
        this.particles = [];
        this.vfPulse   = 0;   // viewfinder pulse phase
        this.resize();
        this.bindEvents();
        this.loop();
    }

    resize() {
        this.W = this.canvas.width  = window.innerWidth;
        this.H = this.canvas.height = window.innerHeight;
        this.buildParticles();
    }

    buildParticles() {
        this.particles = [];
        const n = Math.max(40, Math.floor((this.W * this.H) / 14000));
        for (let i = 0; i < n; i++) {
            this.particles.push({
                x:  Math.random() * this.W,
                y:  Math.random() * this.H,
                vx: (Math.random() - 0.5) * 0.28,
                vy: (Math.random() - 0.5) * 0.28,
                r:  1.2 + Math.random() * 1.4,
                ph: Math.random() * Math.PI * 2,
            });
        }
    }

    drawNetwork() {
        const { ctx, particles, mouse, W, H, t } = this;
        const LINK_DIST   = Math.min(W, H) * 0.16;
        const MOUSE_DIST  = 180;
        const REPEL       = 0.38;

        for (const p of particles) {
            // Gentle drift
            p.x += p.vx + Math.sin(t * 0.22 + p.ph) * 0.06;
            p.y += p.vy + Math.cos(t * 0.18 + p.ph) * 0.06;

            // Mouse repulsion
            const mdx = p.x - mouse.x;
            const mdy = p.y - mouse.y;
            const md  = Math.hypot(mdx, mdy);
            if (md < MOUSE_DIST && md > 0) {
                const f = ((MOUSE_DIST - md) / MOUSE_DIST) * REPEL;
                p.x += (mdx / md) * f;
                p.y += (mdy / md) * f;
            }

            // Wrap with margin
            const m = 40;
            if (p.x < -m) p.x = W + m;
            if (p.x > W + m) p.x = -m;
            if (p.y < -m) p.y = H + m;
            if (p.y > H + m) p.y = -m;
        }

        // Draw lines between nearby particles
        ctx.save();
        for (let i = 0; i < particles.length; i++) {
            for (let j = i + 1; j < particles.length; j++) {
                const a = particles[i], b = particles[j];
                const dx = a.x - b.x, dy = a.y - b.y;
                const dist = Math.hypot(dx, dy);
                if (dist > LINK_DIST) continue;
                const alpha = (1 - dist / LINK_DIST) * 0.13;
                ctx.beginPath();
                ctx.moveTo(a.x, a.y);
                ctx.lineTo(b.x, b.y);
                ctx.strokeStyle = `rgba(200,169,110,${alpha})`;
                ctx.lineWidth = 0.7;
                ctx.stroke();
            }
        }
        ctx.restore();

        // Draw particle dots
        ctx.save();
        for (const p of particles) {
            ctx.beginPath();
            ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
            ctx.fillStyle = `rgba(200,169,110,0.45)`;
            ctx.fill();
        }
        ctx.restore();
    }

    drawViewfinder() {
        const { ctx, W, H, t } = this;
        this.vfPulse += 0.012;

        const cx   = W * 0.5;
        const cy   = H * 0.5;
        const pulse = Math.sin(this.vfPulse) * 0.5 + 0.5;  // 0..1

        ctx.save();
        ctx.lineWidth = 1;

        // ── Corner brackets ──────────────────────────────────
        const bW   = Math.min(W, H) * 0.09;  // bracket arm length
        const bOff = Math.min(W, H) * 0.08;  // offset from corner

        const brackets = [
            { x: bOff,     y: bOff,     dx:  1,  dy:  1 },
            { x: W - bOff, y: bOff,     dx: -1,  dy:  1 },
            { x: bOff,     y: H - bOff, dx:  1,  dy: -1 },
            { x: W - bOff, y: H - bOff, dx: -1,  dy: -1 },
        ];

        const bAlpha = 0.22 + pulse * 0.06;
        ctx.strokeStyle = `rgba(200,169,110,${bAlpha})`;
        ctx.lineWidth = 1.2;

        for (const b of brackets) {
            ctx.beginPath();
            ctx.moveTo(b.x + b.dx * bW, b.y);
            ctx.lineTo(b.x, b.y);
            ctx.lineTo(b.x, b.y + b.dy * bW);
            ctx.stroke();

            // Small corner dot
            ctx.beginPath();
            ctx.arc(b.x, b.y, 2.2, 0, Math.PI * 2);
            ctx.fillStyle = `rgba(200,169,110,${bAlpha * 1.4})`;
            ctx.fill();
        }

        // ── Center crosshair ─────────────────────────────────
        const cLen  = Math.min(W, H) * 0.04;
        const cGap  = 10;
        const cAlpha = 0.14 + pulse * 0.05;

        ctx.strokeStyle = `rgba(200,169,110,${cAlpha})`;
        ctx.lineWidth = 0.8;
        ctx.setLineDash([2, 4]);

        // Horizontal arms
        ctx.beginPath();
        ctx.moveTo(cx - cLen - cGap, cy);
        ctx.lineTo(cx - cGap, cy);
        ctx.moveTo(cx + cGap, cy);
        ctx.lineTo(cx + cLen + cGap, cy);
        // Vertical arms
        ctx.moveTo(cx, cy - cLen - cGap);
        ctx.lineTo(cx, cy - cGap);
        ctx.moveTo(cx, cy + cGap);
        ctx.lineTo(cx, cy + cLen + cGap);
        ctx.stroke();
        ctx.setLineDash([]);

        // ── Center circle ─────────────────────────────────────
        const cR = Math.min(W, H) * 0.055 + pulse * 4;
        ctx.beginPath();
        ctx.arc(cx, cy, cR, 0, Math.PI * 2);
        ctx.strokeStyle = `rgba(200,169,110,${cAlpha * 0.8})`;
        ctx.lineWidth = 0.7;
        ctx.stroke();

        // Outer rule circle (larger, very faint)
        ctx.beginPath();
        ctx.arc(cx, cy, cR * 2.8, 0, Math.PI * 2);
        ctx.strokeStyle = `rgba(200,169,110,${cAlpha * 0.25})`;
        ctx.lineWidth = 0.5;
        ctx.stroke();

        // ── Rule-of-thirds grid (very faint) ─────────────────
        ctx.strokeStyle = `rgba(200,169,110,0.03)`;
        ctx.lineWidth = 0.5;
        for (let i = 1; i <= 2; i++) {
            ctx.beginPath();
            ctx.moveTo(W * i / 3, 0); ctx.lineTo(W * i / 3, H);
            ctx.moveTo(0, H * i / 3); ctx.lineTo(W, H * i / 3);
            ctx.stroke();
        }

        ctx.restore();
    }

    loop() {
        this.t += 0.008;
        this.ctx.clearRect(0, 0, this.W, this.H);
        this.drawViewfinder();
        this.drawNetwork();
        requestAnimationFrame(() => this.loop());
    }

    bindEvents() {
        window.addEventListener('resize',    () => this.resize(), { passive: true });
        window.addEventListener('mousemove', e => {
            this.mouse.x = e.clientX;
            this.mouse.y = e.clientY;
        }, { passive: true });
    }
}

/* ── CUSTOM CURSOR ────────────────────────────────────────── */

class CustomCursor {
    constructor() {
        this.dot  = document.querySelector('.cursor-dot');
        this.ring = document.querySelector('.cursor-ring');
        if (!this.dot || !this.ring) return;

        this.mx = 0; this.my = 0;
        this.rx = 0; this.ry = 0;
        this.rr = 22;   // ring radius (half width)
        this.trr = 22;  // target ring radius
        this.spd = 0.11;

        this.bindEvents();
        this.tick();
    }

    bindEvents() {
        document.addEventListener('mousemove', e => {
            this.mx = e.clientX;
            this.my = e.clientY;
        }, { passive: true });

        document.addEventListener('mouseleave', () => {
            this.dot.style.opacity  = '0';
            this.ring.style.opacity = '0';
        });
        document.addEventListener('mouseenter', () => {
            this.dot.style.opacity  = '1';
            this.ring.style.opacity = '1';
        });

        const label = this.ring.querySelector('.cursor-label');

        const addState = (sel, cls, rr, txt) => {
            document.querySelectorAll(sel).forEach(el => {
                el.addEventListener('mouseenter', () => {
                    this.ring.classList.add(cls);
                    this.trr = rr;
                    if (txt && label) label.textContent = txt;
                });
                el.addEventListener('mouseleave', () => {
                    this.ring.classList.remove(cls);
                    this.trr = 22;
                    if (txt && label) label.textContent = 'VIEW';
                });
            });
        };

        addState('a:not(.carousel-slide):not(.gallery-item), button, .carousel-btn', 'hover-link', 30);
        addState('.photo-item, .carousel-slide, a.gallery-item, .showcase-item', 'hover-view', 40, 'VIEW');
    }

    tick() {
        this.rx  += (this.mx - this.rx)  * this.spd;
        this.ry  += (this.my - this.ry)  * this.spd;
        this.rr  += (this.trr - this.rr) * 0.14;

        this.dot.style.transform  = `translate(${this.mx - 3}px, ${this.my - 3}px)`;
        this.ring.style.transform = `translate(${this.rx - this.rr}px, ${this.ry - this.rr}px)`;

        requestAnimationFrame(() => this.tick());
    }
}

/* ── LOADER ───────────────────────────────────────────────── */

function initLoader(onDone) {
    const loader = document.getElementById('loader');
    const numEl  = document.getElementById('loaderNum');
    const barEl  = document.getElementById('loaderBar');
    if (!loader) { onDone(); return; }

    let count = 0;
    // Ease-out timing: fast start, slow finish
    function tick() {
        if (count >= 100) {
            setTimeout(() => {
                loader.classList.add('hidden');
                onDone();
            }, 320);
            return;
        }
        count++;
        if (numEl) numEl.textContent = String(count).padStart(3, '0');
        if (barEl) barEl.style.width = count + '%';
        // Ease: early=12ms, late=32ms
        const delay = 10 + Math.pow(count / 100, 2.2) * 26;
        setTimeout(tick, delay);
    }
    tick();
}

/* ── HEADER SCROLL STATE ──────────────────────────────────── */

function initHeader() {
    const header = document.querySelector('header');
    if (!header) return;
    const onScroll = () => {
        header.classList.toggle('scrolled', window.scrollY > 40);
    };
    window.addEventListener('scroll', onScroll, { passive: true });
    onScroll();
}

/* ── HERO REVEAL ──────────────────────────────────────────── */

function revealHero() {
    const eyebrow  = document.querySelector('.hero-eyebrow');
    const reveals  = document.querySelectorAll('.hero-reveal');
    const meta     = document.querySelector('.hero-meta');
    const cue      = document.querySelector('.scroll-cue');

    if (eyebrow) {
        setTimeout(() => eyebrow.classList.add('is-visible'), 100);
    }
    reveals.forEach((el, i) => {
        setTimeout(() => { el.style.transform = 'translateY(0)'; }, 180 + i * 130);
    });
    if (meta)  setTimeout(() => meta.classList.add('is-visible'),  560);
    if (cue)   setTimeout(() => cue.classList.add('is-visible'),   900);
}

/* ── SCROLL REVEAL ────────────────────────────────────────── */

function initScrollReveal() {
    const targets = document.querySelectorAll('.reveal, .animate-on-scroll, .reveal-clip');
    if (!targets.length) return;

    const io = new IntersectionObserver((entries) => {
        entries.forEach(e => {
            if (e.isIntersecting) {
                e.target.classList.add('is-visible');
                io.unobserve(e.target);
            }
        });
    }, { threshold: 0.07, rootMargin: '0px 0px -40px 0px' });

    targets.forEach(el => io.observe(el));
}

/* ── PAGE TRANSITIONS ─────────────────────────────────────── */

function initPageTransitions() {
    window.addEventListener('pageshow', e => {
        if (e.persisted) {
            document.body.classList.remove('fade-in');
            requestAnimationFrame(() => {
                requestAnimationFrame(() => document.body.classList.add('fade-in'));
            });
        }
    });

    document.querySelectorAll('a[href]').forEach(link => {
        const href = link.getAttribute('href');
        if (!href || link.target === '_blank') return;
        if (href.startsWith('#') || href.startsWith('mailto:') || href.startsWith('tel:')) return;
        try {
            const url = new URL(href, window.location.href);
            if (url.hostname !== window.location.hostname) return;
        } catch { return; }

        link.addEventListener('click', e => {
            if (link._wasDragging) return;
            e.preventDefault();
            const dest = new URL(href, window.location.href).href;
            document.body.classList.add('page-exit');
            setTimeout(() => window.location.assign(dest), 320);
        });
    });
}

/* ── CAROUSEL ─────────────────────────────────────────────── */

class Carousel {
    constructor() {
        this.vp      = document.getElementById('carouselViewport');
        this.track   = document.getElementById('carouselTrack');
        this.btnPrev = document.getElementById('carouselPrev');
        this.btnNext = document.getElementById('carouselNext');
        this.counter = document.getElementById('carouselCounter');
        if (!this.vp || !this.track) return;

        this.slides  = [...this.track.querySelectorAll('.carousel-slide')];
        this.total   = this.slides.length;
        this.current = 0;
        this.GAP     = 14;

        this.drag    = { on: false, startX: 0, startOff: 0, moved: false };

        requestAnimationFrame(() => {
            this.go(0, false);
            this.bindEvents();
        });
    }

    sw()   { return this.slides[0]?.offsetWidth || 0; }
    center(){ return (this.vp.offsetWidth - this.sw()) / 2; }
    off(i) { return this.center() - i * (this.sw() + this.GAP); }

    go(idx, animate = true) {
        this.current = Math.max(0, Math.min(idx, this.total - 1));
        this.track.style.transition = animate
            ? `transform 0.92s cubic-bezier(0.77,0,0.175,1)` : 'none';
        this.track.style.transform = `translateX(${this.off(this.current)}px)`;
        this.slides.forEach((s, i) => s.classList.toggle('is-active', i === this.current));
        if (this.btnPrev) this.btnPrev.disabled = this.current === 0;
        if (this.btnNext) this.btnNext.disabled = this.current === this.total - 1;
        if (this.counter) {
            const p = n => String(n + 1).padStart(2, '0');
            const t = n => String(n).padStart(2, '0');
            this.counter.textContent = `${p(this.current)} / ${t(this.total)}`;
        }
        // Update dots
        document.querySelectorAll('.carousel-dot')
            .forEach((d, i) => d.classList.toggle('is-active', i === this.current));
    }

    bindEvents() {
        if (this.btnPrev) this.btnPrev.addEventListener('click', () => this.go(this.current - 1));
        if (this.btnNext) this.btnNext.addEventListener('click', () => this.go(this.current + 1));

        document.addEventListener('keydown', e => {
            if (e.key === 'ArrowLeft')  this.go(this.current - 1);
            if (e.key === 'ArrowRight') this.go(this.current + 1);
        });

        // Mouse drag — tylko lewy przycisk, blokuj natywne drag przeglądarki
        this.vp.addEventListener('mousedown', e => {
            if (e.button !== 0) return;
            e.preventDefault();
            this.dragStart(e.clientX);
        });
        window.addEventListener('mousemove', e => { if (this.drag.on) this.dragMove(e.clientX); });
        window.addEventListener('mouseup',   e => { if (this.drag.on) this.dragEnd(e.clientX); });
        // Anuluj drag jeśli mysz opuści okno przeglądarki
        window.addEventListener('mouseleave', () => {
            if (this.drag.on) this.dragEnd(this.drag.startX);
        });

        // Touch
        this.vp.addEventListener('touchstart', e => this.dragStart(e.touches[0].clientX), { passive: true });
        window.addEventListener('touchmove',   e => { if (this.drag.on) this.dragMove(e.touches[0].clientX); }, { passive: true });
        window.addEventListener('touchend',    e => { if (this.drag.on) this.dragEnd(e.changedTouches[0].clientX); });

        // Prevent link nav during drag
        this.slides.forEach(s => {
            s.addEventListener('click', e => {
                if (this.drag.moved) { e.preventDefault(); e.stopPropagation(); }
            });
        });

        window.addEventListener('resize', () => this.go(this.current, false), { passive: true });
    }

    dragStart(x) {
        this.drag = { on: true, startX: x, startOff: this.off(this.current), moved: false };
        this.vp.classList.add('is-dragging');
        this.track.style.transition = 'none';
    }
    dragMove(x) {
        const d = x - this.drag.startX;
        if (Math.abs(d) > 5) this.drag.moved = true;
        this.track.style.transform = `translateX(${this.drag.startOff + d}px)`;
    }
    dragEnd(x) {
        this.drag.on = false;
        this.vp.classList.remove('is-dragging');
        const d   = x - this.drag.startX;
        const thr = this.sw() * 0.13;
        if      (d < -thr) this.go(this.current + 1);
        else if (d >  thr) this.go(this.current - 1);
        else                this.go(this.current);
    }
}

/* ── LIGHTBOX ─────────────────────────────────────────────── */

function initLightbox() {
    if (window._lbLoaded) return; // lightbox.js handles this page
    const items   = document.querySelectorAll('.photo-item');
    const lb      = document.getElementById('lightbox');
    const lbImg   = document.getElementById('lightbox-image');
    const lbClose = document.getElementById('lightbox-close');
    const lbPrev  = document.getElementById('lightbox-prev');
    const lbNext  = document.getElementById('lightbox-next');
    const lbCount = document.getElementById('lightbox-counter');
    if (!lb || !items.length) return;

    const imgs = [...items].map(el => el.querySelector('img').src);
    let cur = 0;

    const show = idx => {
        cur = ((idx % imgs.length) + imgs.length) % imgs.length;
        lbImg.style.opacity = '0';
        setTimeout(() => {
            lbImg.src = imgs[cur];
            lbImg.style.opacity = '1';
            if (lbCount) lbCount.textContent =
                `${String(cur+1).padStart(2,'0')} / ${String(imgs.length).padStart(2,'0')}`;
        }, 220);
    };

    const open = idx => {
        cur = idx;
        lbImg.src = imgs[cur];
        if (lbCount) lbCount.textContent =
            `${String(cur+1).padStart(2,'0')} / ${String(imgs.length).padStart(2,'0')}`;
        lb.classList.add('active');
        document.body.style.overflow = 'hidden';
    };

    const close = () => {
        lb.classList.remove('active');
        document.body.style.overflow = '';
    };

    items.forEach((item, i) => item.addEventListener('click', () => open(i)));
    if (lbClose) lbClose.addEventListener('click', close);
    if (lbPrev)  lbPrev.addEventListener('click', () => show(cur - 1));
    if (lbNext)  lbNext.addEventListener('click', () => show(cur + 1));
    lb.addEventListener('click', e => { if (e.target === lb) close(); });

    document.addEventListener('keydown', e => {
        if (!lb.classList.contains('active')) return;
        if (e.key === 'ArrowRight') show(cur + 1);
        if (e.key === 'ArrowLeft')  show(cur - 1);
        if (e.key === 'Escape')     close();
    });

    // Touch swipe
    let sx = 0;
    lbImg.addEventListener('touchstart', e => { sx = e.touches[0].pageX; }, { passive: true });
    lbImg.addEventListener('touchend',   e => {
        const d = e.changedTouches[0].pageX - sx;
        if (d < -50) show(cur + 1);
        if (d >  50) show(cur - 1);
    });
}

/* ── BOOT ─────────────────────────────────────────────────── */

document.addEventListener('DOMContentLoaded', () => {
    // Start canvas immediately (visible under loader)
    new ParticleViewfinderCanvas('bg-canvas');

    // Cursor
    new CustomCursor();

    // Header scroll
    initHeader();

    // Page transitions
    initPageTransitions();

    // Scroll reveals (for sub-pages that have no loader)
    if (!document.getElementById('loader')) {
        document.body.classList.add('fade-in');
        initScrollReveal();
    }

    // Lightbox (proj pages)
    initLightbox();

    // Loader → then boot interactive features
    initLoader(() => {
        document.body.classList.add('fade-in');
        revealHero();
        initScrollReveal();
        new Carousel();
    });
});
