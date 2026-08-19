// Theme Management
function toggleTheme() {
    const currentTheme = document.documentElement.getAttribute('data-theme');
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';

    document.documentElement.setAttribute('data-theme', newTheme);
    localStorage.setItem('theme', newTheme);

    // Update icons if they exist
    const themeIcons = document.querySelectorAll('.ph-moon-stars, .ph-sun');
    themeIcons.forEach(icon => {
        if (newTheme === 'dark') {
            icon.classList.replace('ph-moon-stars', 'ph-sun');
        } else {
            icon.classList.replace('ph-sun', 'ph-moon-stars');
        }
    });

    showToast(newTheme === 'dark' ? 'Dark Mode Activated' : 'Light Mode Activated', 'info', 'Theme Update');
}

// Initialize Theme on Load
(function initTheme() {
    const savedTheme = localStorage.getItem('theme') || 'light';
    document.documentElement.setAttribute('data-theme', savedTheme);

    window.addEventListener('DOMContentLoaded', () => {
        const themeIcons = document.querySelectorAll('.ph-moon-stars');
        if (savedTheme === 'dark') {
            themeIcons.forEach(icon => icon.classList.replace('ph-moon-stars', 'ph-sun'));
        }
        document.querySelectorAll('i.ph').forEach(icon => {
            if (!icon.hasAttribute('aria-hidden')) icon.setAttribute('aria-hidden', 'true');
        });
    });
})();

// Creative Toast System (Slow Rise & 2s Stay)
function showToast(message, type = 'info', customHeading = null) {
    const container = document.querySelector('.toast-container');
    if (!container) return;

    const toast = document.createElement('div');
    // Use toast-primary for the reddish orange theme defined in premium.css
    const variantClass = 'toast-primary';
    toast.className = `creative-toast p-3 d-flex align-items-center ${variantClass}`;

    let icon = 'ph-info-circle';
    let heading = customHeading;

    // Modern Thin Icons for Premium Look
    const icons = {
        'success': 'ph-check-circle',
        'danger': 'ph-x-circle',
        'warning': 'ph-warning-circle',
        'info': 'ph-info'
    };

    icon = icons[type] || icons['info'];

    let animationClass = '';
    if (type === 'success') {
        animationClass = 'animate-pulse-subtle';
        if (!heading) heading = 'Success';
    } else if (type === 'danger') {
        animationClass = 'animate-shake';
        if (!heading) heading = 'Action Blocked';
    } else if (type === 'warning') {
        if (!heading) heading = 'Warning';
    } else {
        if (!heading) heading = 'System Info';
    }

    toast.innerHTML = `
        <div class="me-3 fs-3 d-flex align-items-center text-white ${animationClass}"><i class="ph ${icon}"></i></div>
        <div class="flex-grow-1 text-white">
            <div class="fw-bold text-uppercase smaller opacity-75 d-flex align-items-center gap-2" style="letter-spacing: 1.5px; font-size: 0.75rem;">
                <span>${heading}</span>
            </div>
            <div class="fw-medium" style="font-size: 0.95rem;">${message}</div>
        </div>
        <button type="button" class="btn-close btn-close-white ms-2" style="font-size: 0.7rem;" onclick="this.parentElement.remove()"></button>
        <div class="toast-progress bg-primary" style="background-color: rgba(255,255,255,0.3) !important;"></div>
    `;

    container.appendChild(toast);

    // Trigger slow rise animation
    setTimeout(() => toast.classList.add('show'), 100);

    // Stay for 3 seconds then disappear
    setTimeout(() => {
        if (toast.parentElement) {
            toast.classList.remove('show');
            setTimeout(() => toast.remove(), 800);
        }
    }, 3000);
}

// Clear History Functionality (REST API)
function clearHistory() {
    if (confirm("Are you sure you want to clear your entire scan history? This action cannot be undone.")) {
        const csrfToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content');
        fetch('/clear_history', { 
            method: 'POST',
            headers: {
                'X-CSRFToken': csrfToken
            }
        })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    showToast(data.message, "success");
                    setTimeout(() => window.location.reload(), 1000);
                } else {
                    showToast(data.message, "danger");
                }
            })
            .catch(err => {
                console.error("Error clearing history:", err);
                showToast("Network error while clearing history.", "danger");
            });
    }
}

// Individual Scan Deletion
function deleteScan(scanId) {
    if (confirm("Are you sure you want to delete this specific scan record?")) {
        // Count unique items across sidebar and modal lists
        const sideItems = document.querySelectorAll('.recent-scans-list .recent-scan-item').length;
        const modalItems = document.querySelectorAll('#modalHistoryList .recent-scan-item').length;
        const itemCount = Math.max(sideItems, modalItems);
        const csrfToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content');

        fetch(`/delete_scan/${scanId}`, { 
            method: 'POST',
            headers: {
                'X-CSRFToken': csrfToken
            }
        })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    showToast(data.message, "success");
                    // If this was the last item, redirect to scan note page
                    if (itemCount <= 1) {
                        setTimeout(() => window.location.href = '/index', 1000);
                    } else {
                        setTimeout(() => window.location.reload(), 1000);
                    }
                } else {
                    showToast(data.message, "danger");
                }
            })
            .catch(err => {
                console.error("Error deleting scan:", err);
                showToast("Network error while deleting scan.", "danger");
            });
    }
}



// Call UI update on load if container exists
$(document).ready(function () {

    // Close modal when clicking on the overlay backdrop
    const historyModal = document.getElementById('historyModal');
    if (historyModal) {
        historyModal.addEventListener('click', function (e) {
            if (e.target === historyModal) {
                closeHistory();
            }
        });
    }

    // Delegation for scan deletion to avoid inline JS lint errors
    $(document).on('click', '.delete-scan-btn', function (e) {
        e.stopPropagation();
        const scanId = $(this).data('scan-id');
        if (scanId) deleteScan(scanId);
    });
});

// History Toggle (Modal Display)
function toggleHistory() {
    const modal = document.getElementById('historyModal');
    if (modal) {
        modal.classList.add('active');
    }
}

function closeHistory() {
    const modal = document.getElementById('historyModal');
    if (modal) modal.classList.remove('active');
}



function viewScanResult(label, filename, score) {
    // Redirect to the new view_result route with score
    let url = `/view_result?prediction=${encodeURIComponent(label)}&filename=${encodeURIComponent(filename)}`;
    if (score && score !== 'undefined') url += `&score=${encodeURIComponent(score)}`;
    window.location.href = url;
}

function previewImage() {
    const file = document.getElementById('imagefile').files[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = function (e) {
        document.getElementById('imagePreview').src = e.target.result;
        document.getElementById('previewContainer').classList.remove('d-none');
        document.getElementById('uploadArea').classList.add('d-none');
        const submitBtn = document.getElementById('submitBtn');
        if (submitBtn) submitBtn.disabled = false;
    };
    reader.readAsDataURL(file);
}

function resetUpload() {
    const uploadArea = document.getElementById('uploadArea');
    const previewContainer = document.getElementById('previewContainer');
    const detectForm = document.querySelector('form[action="/submit"]');
    const imagefile = document.getElementById('imagefile');

    if (detectForm) detectForm.reset();
    if (imagefile) imagefile.value = "";
    if (uploadArea) uploadArea.classList.remove('d-none');
    if (previewContainer) previewContainer.classList.add('d-none');

    const submitBtn = document.getElementById('submitBtn');
    if (submitBtn) submitBtn.disabled = true;
}

function startAnalysisFeedback() {
    const btn = document.getElementById('submitBtn');
    const content = document.getElementById('submitBtnContent');
    const loading = document.getElementById('submitBtnLoading');

    if (btn) {
        btn.disabled = true;
        btn.classList.add('is-processing');
    }
    if (content) content.classList.add('d-none');
    if (loading) loading.classList.remove('d-none');
}

// Hero Slideshow Logic
$(document).ready(function () {
    let slides = $('.hero-slide');
    if (slides.length > 0) {
        let currentIndex = 0;
        setInterval(() => {
            slides.eq(currentIndex).removeClass('active');
            currentIndex = (currentIndex + 1) % slides.length;
            slides.eq(currentIndex).addClass('active');
        }, 4000);
    }
});

// Sidebar Mobile Toggle
window.toggleSidebar = function () {
    $('.sidebar').toggleClass('open');
}

// Preloader Concealment
$(window).on('load', function () {
    $('.preloader').fadeOut('slow');
});

// Safety Fallback & DOMContentLoaded listener
document.addEventListener('DOMContentLoaded', function () {
    // Hide if already loaded or if DOM is ready
    setTimeout(function () {
        if ($('.preloader').is(':visible')) {
            $('.preloader').fadeOut('medium');
            console.log('Preloader hidden via DOMContentLoaded fallback');
        }
    }, 2500); // 2.5 second absolute limit
});

setTimeout(function () {
    if ($('.preloader').is(':visible')) {
        $('.preloader').fadeOut('slow');
        console.log('Preloader hidden via safety timeout');
    }
}, 4000); // 4 second absolute limit

// Number Counter Animation
document.addEventListener('DOMContentLoaded', () => {
    const counters = document.querySelectorAll('.counter-anim');
    if (counters.length === 0) return;

    const observer = new IntersectionObserver((entries, observer) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const targetElement = entry.target;
                const targetValue = parseFloat(targetElement.getAttribute('data-target'));
                const duration = 1500; // Total animation duration in ms
                const frameDuration = 1000 / 60; // Assume 60fps
                const totalFrames = Math.round(duration / frameDuration);
                let currentFrame = 0;

                const easeOutQuad = t => t * (2 - t);

                const countTo = () => {
                    currentFrame++;
                    const progress = easeOutQuad(currentFrame / totalFrames);
                    const currentVal = (targetValue * progress).toFixed(1);

                    targetElement.innerText = currentVal;

                    if (currentFrame < totalFrames) {
                        requestAnimationFrame(countTo);
                    } else {
                        targetElement.innerText = targetValue.toFixed(1);
                    }
                };

                requestAnimationFrame(countTo);
                observer.unobserve(targetElement); // Only animate once
            }
        });
    }, { threshold: 0.1 });

    counters.forEach(counter => {
        observer.observe(counter);
    });
});

// Drag and Drop Logic
document.addEventListener('DOMContentLoaded', () => {
    const dropZone = document.getElementById('dropZone');
    const imagefile = document.getElementById('imagefile');

    if (dropZone && imagefile) {
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            dropZone.addEventListener(eventName, preventDefaults, false);
        });

        function preventDefaults(e) {
            e.preventDefault();
            e.stopPropagation();
        }

        ['dragenter', 'dragover'].forEach(eventName => {
            dropZone.addEventListener(eventName, highlight, false);
        });

        ['dragleave', 'drop'].forEach(eventName => {
            dropZone.addEventListener(eventName, unhighlight, false);
        });

        function highlight(e) {
            dropZone.classList.add('drag-over');
        }

        function unhighlight(e) {
            dropZone.classList.remove('drag-over');
        }

        dropZone.addEventListener('drop', handleDrop, false);

        function handleDrop(e) {
            let dt = e.dataTransfer;
            let files = dt.files;

            if (files && files.length > 0) {
                imagefile.files = files;
                if (typeof previewImage === 'function') {
                    previewImage();
                }
            }
        }
    }
});
