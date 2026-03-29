/* ── BOOTSTRAP VALIDATION ───────────────────────────────────────────────── */
(() => {
    'use strict';
    const forms = document.querySelectorAll('.needs-validation');
    Array.from(forms).forEach(form => {
        form.addEventListener('submit', event => {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            form.classList.add('was-validated');
        }, false);
    });
})();


/* ── LOADER HIDE ────────────────────────────────────────────────────────── */
window.addEventListener('load', function () {
    const loader = document.getElementById('loader');
    if (loader) {
        setTimeout(() => loader.classList.add('hide-loader'), 2000);
    }
});


/* ── DROP ZONE (submit-form) ────────────────────────────────────────────── */
document.addEventListener('DOMContentLoaded', function () {
    const dropZone  = document.getElementById('dropZone');
    const fileInput = document.getElementById('fileInput');
    const fileList  = document.getElementById('fileList');

    if (!dropZone) return;

    dropZone.addEventListener('click', () => fileInput.click());

    fileInput.addEventListener('change', () => renderFileTags(fileInput.files));

    dropZone.addEventListener('dragover', e => {
        e.preventDefault();
        dropZone.style.borderColor = '#198754';
    });

    dropZone.addEventListener('dragleave', () => {
        dropZone.style.borderColor = '';
    });

    dropZone.addEventListener('drop', e => {
        e.preventDefault();
        dropZone.style.borderColor = '';
        fileInput.files = e.dataTransfer.files;
        renderFileTags(e.dataTransfer.files);
    });

    function getFileIcon(name) {
        const ext = name.split('.').pop().toLowerCase();
        if (['jpg', 'jpeg', 'png', 'gif', 'webp'].includes(ext)) return 'bi-image';
        if (['mp4', 'webm', 'mov'].includes(ext))                 return 'bi-camera-video';
        if (ext === 'pdf')                                        return 'bi-file-earmark-pdf';
        return 'bi-file-earmark';
    }

    function renderFileTags(files) {
        fileList.innerHTML = '';
        if (!files || files.length === 0) return;
        Array.from(files).forEach(f => {
            const tag = document.createElement('div');
            tag.className = 'file-tag';
            tag.innerHTML = `<i class="bi ${getFileIcon(f.name)}"></i><span title="${f.name}">${f.name}</span>`;
            fileList.appendChild(tag);
        });
    }
});


/* ── CAPTCHA MODULE (submit-form) ───────────────────────────────────────── */
const Captcha = (() => {
    let token    = null;
    let verified = false;
    const el = id => document.getElementById(id);

    function setStatus(msg, cls = '') {
        const s = el('captchaStatus');
        if (!s) return;
        s.textContent = msg;
        s.className   = 'captcha-status ' + cls;
    }

    async function load() {
        if (!el('captchaStatus')) return; // not on this page
        verified = false;
        el('captchaToken').value = '';
        el('captchaX').value     = '';
        el('captchaY').value     = '';
        el('captchaImg').style.display      = 'none';
        el('captchaSkeleton').style.display = 'block';
        el('captchaImgWrap').classList.remove('clicked');
        el('captchaClickDot').style.display = 'none';
        setStatus('Loading challenge…');

        try {
            const res  = await fetch('/captcha/challenge');
            const data = await res.json();
            token = data.token;
            el('captchaToken').value = data.token;
            const img = el('captchaImg');
            img.onload = () => {
                el('captchaSkeleton').style.display = 'none';
                img.style.display = 'block';
                el('captchaPrompt').innerHTML = data.prompt;
                setStatus('Click the shape shown above');
            };
            img.src = data.image;
        } catch (e) {
            setStatus('Failed to load — click New to retry', 'err');
        }
    }

    function handleClick(e) {
        if (verified) return;
        const wrap = el('captchaImgWrap');
        const rect = wrap.getBoundingClientRect();
        const cx   = (e.clientX - rect.left) * (320 / rect.width);
        const cy   = (e.clientY - rect.top)  * (180 / rect.height);
        const dot  = el('captchaClickDot');
        dot.style.left    = `${e.clientX - rect.left}px`;
        dot.style.top     = `${e.clientY - rect.top}px`;
        dot.style.display = 'block';
        wrap.classList.add('clicked');
        verified = true;
        el('captchaX').value = cx;
        el('captchaY').value = cy;
        setStatus('✓ Click recorded — submit when ready', 'ok');
    }

    return { load, handleClick, isVerified: () => verified };
})();


/* ── SUBMIT FORM (submit-form) ──────────────────────────────────────────── */
document.addEventListener('DOMContentLoaded', function () {
    const imgWrap    = document.getElementById('captchaImgWrap');
    const refreshBtn = document.getElementById('captchaRefreshBtn');
    const form       = document.getElementById('reportForm');

    if (!form) return; // not on submit page

    Captcha.load();
    imgWrap.addEventListener('click', Captcha.handleClick);
    refreshBtn.addEventListener('click', Captcha.load);

    form.addEventListener('submit', function (e) {
        e.preventDefault();

        // Honeypot check
        if (document.getElementById('website').value) return;

        // CAPTCHA check
        if (!Captcha.isVerified()) {
            const s = document.getElementById('captchaStatus');
            s.textContent = '⚠ Please complete the CAPTCHA first';
            s.className   = 'captcha-status err';
            imgWrap.scrollIntoView({ behavior: 'smooth', block: 'center' });
            return;
        }

        fetch('/submit-report', {
            method: 'POST',
            body:   new FormData(form)
        })
        .then(r => r.json())
        .then(data => {
            if (data.success) {
                document.getElementById('trackingDisplay').innerText = data.tracking_id;
                new bootstrap.Modal(document.getElementById('tracking-key')).show();
            } else {
                alert(data.error || 'Submission failed. Please try again.');
                Captcha.load();
            }
        })
        .catch(err => console.error('Submit error:', err));
    });

    // Copy tracking ID and redirect
    document.addEventListener('click', function (e) {
        if (e.target && e.target.id === 'copyBtn') {
            const id = document.getElementById('trackingDisplay').innerText;
            navigator.clipboard.writeText(id).then(() => {
                setTimeout(() => { window.location.href = '/'; }, 500);
            }).catch(err => console.error('Copy failed', err));
        }
    });
});


/* ── STATUS FORM (status-form) ──────────────────────────────────────────── */
document.addEventListener('DOMContentLoaded', function () {
    const form = document.getElementById('status-report');
    if (!form) return;

    form.addEventListener('submit', function (e) {
        e.preventDefault();
        fetch('/status-reports', {
            method: 'POST',
            body:   new FormData(form)
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                document.getElementById('status-badge').innerText = data.status;
                document.getElementById('Note').innerText         = data.note;
            }
        });
    });
});


/* ── SELECT2 ROLE SELECT ────────────────────────────────────────────────── */
document.addEventListener('DOMContentLoaded', function () {
    if (typeof $ === 'undefined' || typeof $.fn.select2 === 'undefined') return;

    function formatOption(option) {
        if (!option.id) return option.text;
        const imageUrl = $(option.element).data('image');
        if (!imageUrl) return option.text;
        return $(
            '<span class="d-flex align-items-center gap-2">' +
            '<img src="' + imageUrl + '" width="25px" height="25px" style="border-radius:50%;">' +
            option.text +
            '</span>'
        );
    }

    $('#roleSelect').select2({
        templateResult:    formatOption,
        templateSelection: formatOption,
        minimumResultsForSearch: Infinity
    });
});


/* ── CHARTS (dashboard / admin pages) ──────────────────────────────────── */
document.addEventListener('DOMContentLoaded', function () {
    const pieEl = document.getElementById('ReportsPieChart');
    if (pieEl && typeof Chart !== 'undefined') {
        new Chart(pieEl, {
            type: 'doughnut',
            data: {
                datasets: [{
                    data: [3, 4, 5],
                    backgroundColor: ['#3b82f6', '#22c55e', '#ef4444', '#a855f7'],
                    hoverOffset: 4
                }],
                labels: ['open', 'closed', 'failed', 'reviewed']
            },
            options: {
                cutout: '65%',
                maintainAspectRatio: false,
                layout: { padding: { top: 10 } },
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            usePointStyle: true,
                            pointStyle: 'circle',
                            boxWidth: 12,
                            boxHeight: 12,
                            padding: 20,
                            font: { size: 12 }
                        }
                    }
                }
            }
        });
    }
});

document.addEventListener('DOMContentLoaded', function () {
    const lineEl = document.getElementById('ReportsGraphChart');
    if (lineEl && typeof Chart !== 'undefined') {
        new Chart(lineEl, {
            type: 'line',
            data: {
                labels: ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'],
                datasets: [{
                    label: 'reports',
                    data: [0, 1, 2, 5, 3, 0, 4],
                    tension: 0.3,
                    fill: true,
                    backgroundColor: '#89b4f9'
                }]
            }
        });
    }
});


/* ── POPUP (pages with openBtn / popup / closeBtn) ──────────────────────── */
document.addEventListener('DOMContentLoaded', function () {
    const openBtn  = document.getElementById('openBtn');
    const popup    = document.getElementById('popup');
    const closeBtn = document.getElementById('closeBtn');

    if (!openBtn || !popup || !closeBtn) return;

    openBtn.onclick = () => { popup.style.display = 'flex'; };
    closeBtn.onclick = () => { popup.style.display = 'none'; };
    window.addEventListener('click', e => {
        if (e.target === popup) popup.style.display = 'none';
    });
});


/* ── PARTICLE SYSTEM (index page) ───────────────────────────────────────── */
class Particle {
    constructor(canvas, ctx, options = {}) {
        this.canvas = canvas;
        this.ctx    = ctx;
        this.x = options.x ?? Math.random() * canvas.width;
        this.y = options.y ?? Math.random() * canvas.height;
        this.size     = options.size ?? (0.5 + Math.random() * 2);
        this.baseSize = this.size;
        this.speedX   = options.speedX ?? (Math.random() - 0.5) * 0.3;
        this.speedY   = options.speedY ?? (Math.random() - 0.5) * 0.3;
        this.color    = options.color ?? this.getRandomColor();
        this.alpha    = options.alpha ?? (0.4 + Math.random() * 0.6);
        this.isNode   = options.isNode ?? (Math.random() > 0.97);
        this.nodeConnections = [];
        this.orbitSpeed  = Math.random() * 0.01 + 0.005;
        this.orbitAngle  = Math.random() * Math.PI * 2;
        this.orbitRadius = 0;
        this.pulseSpeed  = 0.03 + Math.random() * 0.04;
        this.pulseDirection = 1;

        if (this.isNode) {
            this.size        = 3 + Math.random() * 4;
            this.orbitRadius = 15 + Math.random() * 25;
            this.speedX      = (Math.random() - 0.5) * 0.1;
            this.speedY      = (Math.random() - 0.5) * 0.1;
        }
    }

    getRandomColor() {
        const colors = ['#6c8ebf', '#7b9fd4', '#a0b8d8', '#8fa8c8', '#b0c4de'];
        return colors[Math.floor(Math.random() * colors.length)];
    }

    draw() {
        this.ctx.beginPath();
        this.ctx.arc(this.x, this.y, this.size, 0, Math.PI * 2);
        this.ctx.fillStyle  = this.color;
        this.ctx.globalAlpha = this.alpha;
        this.ctx.fill();
        if (this.isNode) this.drawOrbiters();
        if (this.isNode && this.nodeConnections.length > 0) this.drawConnections();
        this.ctx.globalAlpha = 1;
    }

    drawOrbiters() {
        const orbiters = 2 + Math.floor(Math.random() * 3);
        for (let i = 0; i < orbiters; i++) {
            const angle = this.orbitAngle + (Math.PI * 2 / orbiters) * i;
            const x = this.x + Math.cos(angle) * this.orbitRadius;
            const y = this.y + Math.sin(angle) * this.orbitRadius;
            this.ctx.beginPath();
            this.ctx.arc(x, y, 0.8, 0, Math.PI * 2);
            this.ctx.fillStyle   = this.color;
            this.ctx.globalAlpha = this.alpha * 0.8;
            this.ctx.fill();
        }
    }

    drawConnections() {
        this.nodeConnections.forEach(node => {
            const dx = this.x - node.x;
            const dy = this.y - node.y;
            const distance = Math.sqrt(dx * dx + dy * dy);
            if (distance < 200) {
                const opacity = 1 - distance / 200;
                this.ctx.beginPath();
                this.ctx.moveTo(this.x, this.y);
                this.ctx.lineTo(node.x, node.y);
                this.ctx.strokeStyle  = this.color;
                this.ctx.globalAlpha  = opacity * 0.15;
                this.ctx.lineWidth    = 0.5;
                this.ctx.stroke();
            }
        });
    }

    update(mouseX, mouseY) {
        this.x += this.speedX;
        this.y += this.speedY;

        if (this.x > this.canvas.width)  this.x = 0;
        if (this.x < 0)                  this.x = this.canvas.width;
        if (this.y > this.canvas.height) this.y = 0;
        if (this.y < 0)                  this.y = this.canvas.height;

        if (this.isNode) {
            this.size += this.pulseDirection * this.pulseSpeed;
            if (this.size > this.baseSize * 1.5 || this.size < this.baseSize * 0.8) {
                this.pulseDirection *= -1;
            }
            this.orbitAngle += this.orbitSpeed;
        }

        if (mouseX !== null && mouseY !== null) {
            const dx = mouseX - this.x;
            const dy = mouseY - this.y;
            const distance = Math.sqrt(dx * dx + dy * dy);
            if (distance < 120) {
                const force = (120 - distance) / 1500;
                this.speedX += dx > 0 ? force : -force;
                this.speedY += dy > 0 ? force : -force;
                this.alpha = Math.min(1, this.alpha + 0.05);
                if (!this.isNode) this.size = Math.min(this.baseSize * 2, this.size + 0.1);
            } else {
                this.alpha = Math.max(this.alpha - 0.01, this.isNode ? 0.4 : 0.2);
                if (!this.isNode) this.size = Math.max(this.baseSize, this.size - 0.05);
            }
        }

        this.speedX *= 0.99;
        this.speedY *= 0.99;
    }
}

class ParticleSystem {
    constructor(canvasId) {
        this.canvas     = document.getElementById(canvasId);
        if (!this.canvas) return;
        this.ctx        = this.canvas.getContext('2d');
        this.particles  = [];
        this.mouseX     = null;
        this.mouseY     = null;
        this.resizeTimer = null;

        this.resize();
        this.createParticles();
        this.connectNodes();
        this.setupEventListeners();
        this.animate();
    }

    resize() {
        this.canvas.width  = window.innerWidth;
        this.canvas.height = window.innerHeight;
    }

    createParticles() {
        const total = Math.min(150, Math.floor((this.canvas.width * this.canvas.height) / 8000));
        for (let i = 0; i < total; i++) {
            this.particles.push(new Particle(this.canvas, this.ctx));
        }
    }

    connectNodes() {
        const nodes = this.particles.filter(p => p.isNode);
        nodes.forEach(node => {
            const count  = 1 + Math.floor(Math.random() * 3);
            const others = nodes.filter(n => n !== node);
            for (let i = 0; i < Math.min(count, others.length); i++) {
                const idx = Math.floor(Math.random() * others.length);
                node.nodeConnections.push(others[idx]);
                others.splice(idx, 1);
            }
        });
    }

    setupEventListeners() {
        window.addEventListener('resize', () => {
            clearTimeout(this.resizeTimer);
            this.resizeTimer = setTimeout(() => this.resize(), 250);
        });
        document.addEventListener('mousemove', e => {
            this.mouseX = e.clientX;
            this.mouseY = e.clientY;
        });
        document.addEventListener('touchmove', e => {
            if (e.touches.length > 0) {
                this.mouseX = e.touches[0].clientX;
                this.mouseY = e.touches[0].clientY;
            }
        });
        document.addEventListener('mouseleave', () => { this.mouseX = null; this.mouseY = null; });
        document.addEventListener('touchend',   () => { this.mouseX = null; this.mouseY = null; });
    }

    animate() {
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
        this.particles.forEach(p => { p.update(this.mouseX, this.mouseY); p.draw(); });
        this.particles = this.particles.filter(p => p.alpha > 0.05);
        requestAnimationFrame(this.animate.bind(this));
    }
}

document.addEventListener('DOMContentLoaded', () => {
    if (document.getElementById('particleCanvas')) {
        new ParticleSystem('particleCanvas');
    }
});


/* ── ADMIN PAGE ─────────────────────────────────────────────────────────── */
document.addEventListener('DOMContentLoaded', function () {
    if (!document.getElementById('admin')) return; // only run on admin page

    let currentTrackingId = null;

    // ── View button → store tracking ID and populate modal ───────────────
    document.querySelectorAll('.view-btn').forEach(btn => {
        btn.addEventListener('click', function () {
            currentTrackingId = this.dataset.trackingId;
            document.getElementById('modal-tracking-id').textContent = currentTrackingId;
            document.getElementById('secret-code-input').value = '';
        });
    });

    // ── Decrypt button → upload key, fetch and display report ────────────
    document.getElementById('decrypt-submit-btn').addEventListener('click', function () {
        const fileInput = document.getElementById('secret-code-input');
        const file = fileInput.files[0];

        if (!file) {
            alert('Please upload your private key (.pem file)');
            return;
        }

        this.textContent = 'Decrypting...';
        this.disabled = true;
        const btn = this;

        const formData = new FormData();
        formData.append('tracking_id', currentTrackingId);
        formData.append('private_key', file);

        fetch('/get-report', { method: 'POST', body: formData })
            .then(res => res.json())
            .then(data => {
                btn.textContent = 'Decrypt Report';
                btn.disabled = false;
                fileInput.value = '';

                if (!data.success) {
                    alert('Error: ' + data.message);
                    return;
                }

                // Populate the decrypted report modal
                document.getElementById('modal-report-id').textContent = currentTrackingId;
                document.querySelector('[data-field="title"]').textContent       = data.title;
                document.querySelector('[data-field="category"]').textContent    = data.category;
                document.querySelector('[data-field="description"]').textContent = data.description;

                const evidenceEl = document.querySelector('[data-field="evidence"]');
                if (data.evidence && data.evidence.startsWith('http')) {
                    evidenceEl.innerHTML = data.evidence.split(',').map(url => {
                        const isImage = /\.(jpg|jpeg|png|gif|webp)$/i.test(url);
                        return isImage
                            ? `<img src="${url}" class="img-fluid rounded mb-2" style="max-height:200px;">`
                            : `<a href="${url}" target="_blank" class="btn btn-sm btn-outline-secondary mb-1">View File</a>`;
                    }).join('');
                } else {
                    evidenceEl.textContent = data.evidence || 'No evidence provided';
                }

                // Close decrypt modal, then open report modal
                const decryptModal = bootstrap.Modal.getInstance(document.getElementById('decryptModal'));
                decryptModal.hide();
                document.getElementById('decryptModal').addEventListener('hidden.bs.modal', function () {
                    new bootstrap.Modal(document.getElementById('reportDecryptedModal')).show();
                }, { once: true });
            })
            .catch(err => {
                btn.textContent = 'Decrypt Report';
                btn.disabled = false;
                alert('Something went wrong.');
                console.error(err);
            });
    });

    // ── Submit note + status update ───────────────────────────────────────
    document.getElementById('update-report-btn').addEventListener('click', function () {
        const note   = document.getElementById('descInput').value.trim();
        const status = document.querySelector('input[name="reportStatus"]:checked');

        if (!status) {
            alert('Please select a status');
            return;
        }

        fetch('/update-report', {
            method: 'POST',
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
            body: `tracking_id=${encodeURIComponent(currentTrackingId)}&status=${encodeURIComponent(status.value)}&note=${encodeURIComponent(note)}`
        })
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    alert('Report updated successfully');
                    bootstrap.Modal.getInstance(document.getElementById('reportDecryptedModal')).hide();
                    location.reload();
                } else {
                    alert('Error: ' + data.message);
                }
            });
    });

    // ── Add admin form ────────────────────────────────────────────────────
    const adminForm = document.getElementById('admin-form');
    if (adminForm) {
        adminForm.addEventListener('submit', function (e) {
            e.preventDefault();
            fetch('/add-admin', { method: 'POST', body: new FormData(adminForm) })
                .then(r => r.json())
                .then(data => {
                    if (data.success) {
                        alert('Admin added successfully');
                        adminForm.reset();
                    } else {
                        alert('Error: ' + data.message);
                    }
                });
        });
    }
});
