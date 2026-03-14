(() => {
    'use strict'

    const forms = document.querySelectorAll('.needs-validation')

    Array.from(forms).forEach(form => {
        form.addEventListener('submit', event => {
            if (!form.checkValidity()) {
                event.preventDefault()
                event.stopPropagation()
            }

            form.classList.add('was-validated')
        }, false)
    })
})()


document.addEventListener("DOMContentLoaded", function () {

    const dropZone = document.getElementById("dropZone");
    const fileInput = document.getElementById("fileInput");
    const fileName = document.getElementById("fileName");

    if (!dropZone) return;

    // Click to open file selector
    dropZone.addEventListener("click", () => fileInput.click());

    // File selected normally
    fileInput.addEventListener("change", function () {
        if (this.files.length > 0) {
            fileName.textContent = this.files[0].name;
        }
    });

    // Drag events
    dropZone.addEventListener("dragover", (e) => {
        e.preventDefault();
        dropZone.classList.add("dragover");
    });

    dropZone.addEventListener("dragleave", () => {
        dropZone.classList.remove("dragover");
    });

    dropZone.addEventListener("drop", (e) => {
        e.preventDefault();
        dropZone.classList.remove("dragover");

        const files = e.dataTransfer.files;
        if (files.length > 0) {
            fileInput.files = files;
            fileName.textContent = files[0].name;
        }
    });

});
document.addEventListener("DOMContentLoaded", function () {
    $(document).ready(function () {

        function formatOption(option) {
            if (!option.id) {
                return option.text;
            }

            var imageUrl = $(option.element).data('image');

            if (!imageUrl) {
                return option.text;
            }

            return $(
                '<span class="d-flex align-items-center gap-2">' +
                '<img src="' + imageUrl + '" width="25px" height="25px" style="border-radius:50%;">' +
                option.text +
                '</span>'
            );
        }

        $('#roleSelect').select2({
            templateResult: formatOption,
            templateSelection: formatOption,
            minimumResultsForSearch: Infinity
        });

    });
});

document.addEventListener("DOMContentLoaded", function () {
    const Piechart = document.getElementById('ReportsPieChart');
    new Chart(Piechart, {
        type: 'doughnut',
        data: {
            datasets: [{
                data: [3, 4, 5],
                backgroundColor: ['#3b82f6', '#22c55e', '#ef4444', '#a855f7'],
                hoverOffset: 4
            }],
            labels: ['open', 'closed', 'failed', 'reviewed'],
        },
        options: {
            cutout: '65%',
            maintainAspectRatio: false,
            layout: {
                padding: {
                    top: 10
                }
            },
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        usePointStyle: true,
                        pointStyle: 'circle',
                        boxWidth: 12,
                        boxHeight: 12,
                        padding: 20,
                        font: {
                            size: 12
                        }
                    }
                }
            }
        }
    })
});

document.addEventListener("DOMContentLoaded", function () {
    const graphChart = document.getElementById('ReportsGraphChart')
    new Chart(graphChart, {
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
    })

});

window.addEventListener("load", function () {
    setTimeout(() => {
        document.getElementById("loader").classList.add("hide-loader");
    }, 2000);
});

const openBtn = document.getElementById("openBtn");
const popup = document.getElementById("popup");
const closeBtn = document.getElementById("closeBtn");

openBtn.onclick = () => {
    popup.style.display = "flex";
};

closeBtn.onclick = () => {
    popup.style.display = "none";
};

window.onclick = (e) => {
    if (e.target === popup) {
        popup.style.display = "none";
    }
};
