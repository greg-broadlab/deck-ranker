// Shared slide viewer — included by index.html and rankings.html

function initViewer() {
    const modal = document.createElement('div');
    modal.id = 'viewer-modal';
    modal.innerHTML = `
        <div class="viewer-header">
            <span class="viewer-title" id="viewer-title"></span>
            <button class="viewer-close" onclick="closeViewer()">&#x2715;</button>
        </div>
        <div class="viewer-slides" id="viewer-slides"></div>
    `;
    document.body.appendChild(modal);
    modal.addEventListener('click', e => { if (e.target === modal) closeViewer(); });
    document.addEventListener('keydown', e => { if (e.key === 'Escape') closeViewer(); });
}

function openViewer(filename, prefix, slideCount) {
    if (!prefix) return;
    document.getElementById('viewer-title').textContent = filename.replace('.pptx', '');
    const slides = document.getElementById('viewer-slides');
    slides.innerHTML = '';
    slides.scrollTop = 0;
    for (let i = 0; i < slideCount; i++) {
        const img = document.createElement('img');
        img.src = slideUrl(prefix, i);
        img.className = 'viewer-slide-img';
        img.loading = i < 3 ? 'eager' : 'lazy';
        slides.appendChild(img);
    }
    document.getElementById('viewer-modal').style.display = 'flex';
}

function closeViewer() {
    document.getElementById('viewer-modal').style.display = 'none';
}
