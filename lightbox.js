/* Shared lightbox logic for projekt pages */
document.addEventListener('DOMContentLoaded', () => {
    const items    = document.querySelectorAll('.photo-item');
    const lightbox = document.getElementById('lightbox');
    const lbImg    = document.getElementById('lightbox-image');
    const closBtn  = document.getElementById('lightbox-close');
    const prevBtn  = document.getElementById('lightbox-prev');
    const nextBtn  = document.getElementById('lightbox-next');

    const images = Array.from(items).map(el => el.querySelector('img').src);
    let current = 0;

    const counter = document.getElementById('lightbox-counter');

    function updateCounter() {
        if (counter) counter.textContent = `${current + 1} / ${images.length}`;
    }

    function show(index) {
        lbImg.style.opacity = '0';
        setTimeout(() => {
            current = (index + images.length) % images.length;
            lbImg.src = images[current];
            lbImg.style.opacity = '1';
            updateCounter();
        }, 200);
    }

    function open(index) {
        current = index;
        lbImg.src = images[current];
        lightbox.classList.add('active');
        document.body.style.overflow = 'hidden';
        updateCounter();
    }

    function close() {
        lightbox.classList.remove('active');
        document.body.style.overflow = '';
    }

    items.forEach((item, i) => item.addEventListener('click', () => open(i)));
    closBtn.addEventListener('click', close);
    nextBtn.addEventListener('click', () => show(current + 1));
    prevBtn.addEventListener('click', () => show(current - 1));

    lightbox.addEventListener('click', e => { if (e.target === lightbox) close(); });

    document.addEventListener('keydown', e => {
        if (!lightbox.classList.contains('active')) return;
        if (e.key === 'ArrowRight') show(current + 1);
        if (e.key === 'ArrowLeft')  show(current - 1);
        if (e.key === 'Escape')     close();
    });

    // Swipe support
    let startX = 0;
    lbImg.addEventListener('touchstart', e => { startX = e.touches[0].pageX; }, { passive: true });
    lbImg.addEventListener('touchend',   e => {
        const dx = e.changedTouches[0].pageX - startX;
        if (dx < -50) show(current + 1);
        if (dx >  50) show(current - 1);
    });
});
