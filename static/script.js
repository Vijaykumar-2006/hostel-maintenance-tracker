// HostelCare - small client-side helpers (the server still validates everything)

document.addEventListener("DOMContentLoaded", function () {
    // Mobile navigation toggle
    const navToggle = document.getElementById("navToggle");
    const navLinks = document.getElementById("navLinks");
    if (navToggle && navLinks) {
        navToggle.addEventListener("click", function () {
            navLinks.classList.toggle("open");
        });
    }

    // Close flash messages
    document.querySelectorAll(".flash-close").forEach(function (button) {
        button.addEventListener("click", function () {
            button.parentElement.remove();
        });
    });

    // Report form: live character counter + validation before submit
    const reportForm = document.getElementById("reportForm");
    if (reportForm) {
        const description = document.getElementById("description");
        const charCount = document.getElementById("charCount");
        const errorBox = document.getElementById("clientErrors");

        const updateCount = function () {
            charCount.textContent = description.value.length;
        };
        description.addEventListener("input", updateCount);
        updateCount();

        reportForm.addEventListener("submit", function (event) {
            const errors = [];
            if (!reportForm.student_name.value.trim()) errors.push("Please enter your name.");
            if (!reportForm.room_number.value.trim()) errors.push("Please enter your block / room number.");
            if (!reportForm.querySelector("input[name='category']:checked")) errors.push("Please select an issue category.");
            if (description.value.trim().length < 10) errors.push("Description must be at least 10 characters.");

            if (errors.length > 0) {
                event.preventDefault();
                errorBox.innerHTML = errors.join("<br>");
                errorBox.classList.remove("hidden");
            }
        });
    }

    // Admin dashboard: instant table search
    const tableSearch = document.getElementById("tableSearch");
    const table = document.getElementById("requestsTable");
    if (tableSearch && table) {
        tableSearch.addEventListener("input", function () {
            const query = tableSearch.value.toLowerCase();
            table.querySelectorAll("tbody tr").forEach(function (row) {
                row.style.display = row.textContent.toLowerCase().includes(query) ? "" : "none";
            });
        });
    }

    // Admin dashboard: confirm before status change
    document.querySelectorAll(".status-form").forEach(function (form) {
        form.addEventListener("submit", function (event) {
            const status = form.querySelector("select").value;
            if (!confirm("Change status to '" + status + "'?")) {
                event.preventDefault();
            }
        });
    });
});
