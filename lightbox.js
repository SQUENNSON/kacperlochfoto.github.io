/* Shared lightbox logic for projekt pages */
document.addEventListener('DOMContentLoaded', () => {
    const items    = document.querySelectorAll('.photo-item');
    const lightbox = document.getElementById('lightbox');
    const lbImg    = document.getElementById('lightbox-image');
    const closBtn  = document.getElementById('lightbox-close');
    const prevBtn  = document.getElementById('lightbox-prev');
    const nextBtn  = document.getElementById('lightbox-next');
    const counter  = document.getElementById('lightbox-counter');

    const images = Array.from(items).map(el => el.querySelector('img').src);
    let current = 0;

    // ── Zoom / Pan state ──────────────────────────────────────
    let scale = 1;
    let tx = 0, ty = 0;
    let isDragging = false;
    let dragStartX, dragStartY, dragTx, dragTy;

    function applyTransform() {
        lbImg.style.transform = `scale(${scale}) translate(${tx}px, ${ty}px)`;
    }

    function resetZoom() {
        scale = 1; tx = 0; ty = 0;
        lbImg.style.transition = 'none';
        applyTransform();
    }

    // ── Counter ───────────────────────────────────────────────
    function updateCounter() {
        if (counter) counter.textContent = `${current + 1} / ${images.length}`;
    }

    // ── Navigation ────────────────────────────────────────────
    function show(index) {
        resetZoom();
        lbImg.style.transition = 'opacity 0.2s ease, transform 0.2s ease';
        lbImg.style.opacity = '0';
        lbImg.style.transform = 'scale(0.96)';
        setTimeout(() => {
            current = (index + images.length) % images.length;
            lbImg.src = images[current];
            lbImg.style.opacity = '1';
            lbImg.style.transform = 'scale(1)';
            updateCounter();
        }, 200);
    }

    function open(index) {
        current = index;
        resetZoom();
        lbImg.src = images[current];
        lbImg.style.transition = 'none';
        lbImg.style.opacity = '1';
        lbImg.style.transform = 'scale(1)';
        lightbox.classList.add('active');
        document.body.style.overflow = 'hidden';
        updateCounter();
    }

    function close() {
        lightbox.classList.remove('active');
        document.body.style.overflow = '';
        resetZoom();
    }

    // ── Scroll to zoom ────────────────────────────────────────
    lightbox.addEventListener('wheel', (e) => {
        e.preventDefault();
        const delta = e.deltaY < 0 ? 0.12 : -0.12;
        scale = Math.min(Math.max(1, scale + delta), 4);
        if (scale === 1) { tx = 0; ty = 0; }
        lbImg.style.transition = 'none';
        applyTransform();
    }, { passive: false });

    // ── Drag to pan (when zoomed) ─────────────────────────────
    lbImg.addEventListener('mousedown', (e) => {
        if (scale <= 1) return;
        isDragging = true;
        dragStartX = e.clientX;
        dragStartY = e.clientY;
        dragTx = tx;
        dragTy = ty;
        e.preventDefault();
    });

    document.addEventListener('mousemove', (e) => {
        if (!isDragging) return;
        tx = dragTx + (e.clientX - dragStartX) / scale;
        ty = dragTy + (e.clientY - dragStartY) / scale;
        lbImg.style.transition = 'none';
        applyTransform();
    });

    document.addEventListener('mouseup', () => {
        isDragging = false;
    });

    // ── Pinch zoom (mobile) ───────────────────────────────────
    let pinchDist = 0;
    lightbox.addEventListener('touchstart', e => {
        if (e.touches.length === 2) {
            pinchDist = Math.hypot(
                e.touches[0].clientX - e.touches[1].clientX,
                e.touches[0].clientY - e.touches[1].clientY
            );
        }
    }, { passive: true });

    lightbox.addEventListener('touchmove', e => {
        if (e.touches.length !== 2) return;
        e.preventDefault();
        const dist = Math.hypot(
            e.touches[0].clientX - e.touches[1].clientX,
            e.touches[0].clientY - e.touches[1].clientY
        );
        scale = Math.min(Math.max(1, scale * (dist / pinchDist)), 4);
        pinchDist = dist;
        if (scale === 1) { tx = 0; ty = 0; }
        lbImg.style.transition = 'none';
        applyTransform();
    }, { passive: false });

    // ── Swipe (mobile, tylko gdy nie zoomed) ──────────────────
    let swipeStartX = 0;
    lightbox.addEventListener('touchstart', e => {
        if (e.touches.length === 1) swipeStartX = e.touches[0].pageX;
    }, { passive: true });

    lightbox.addEventListener('touchend', e => {
        if (scale > 1) return;
        const dx = e.changedTouches[0].pageX - swipeStartX;
        if (dx < -50) show(current + 1);
        if (dx >  50) show(current - 1);
    });

    // ── Keyboard ──────────────────────────────────────────────
    document.addEventListener('keydown', e => {
        if (!lightbox.classList.contains('active')) return;
        if (e.key === 'ArrowRight') show(current + 1);
        if (e.key === 'ArrowLeft')  show(current - 1);
        if (e.key === 'Escape')     close();
        if (e.key === '+' || e.key === '=') {
            scale = Math.min(scale + 0.3, 4);
            lbImg.style.transition = 'transform 0.2s ease';
            applyTransform();
        }
        if (e.key === '-') {
            scale = Math.max(scale - 0.3, 1);
            if (scale === 1) { tx = 0; ty = 0; }
            lbImg.style.transition = 'transform 0.2s ease';
            applyTransform();
        }
    });

    // ── Click handlers ────────────────────────────────────────
    items.forEach((item, i) => item.addEventListener('click', () => open(i)));
    closBtn.addEventListener('click', close);
    nextBtn.addEventListener('click', () => { resetZoom(); show(current + 1); });
    prevBtn.addEventListener('click', () => { resetZoom(); show(current - 1); });

    lightbox.addEventListener('click', e => {
        if (e.target === lightbox) close();
    });
});
