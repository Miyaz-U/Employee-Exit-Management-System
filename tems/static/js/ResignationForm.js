document.addEventListener("DOMContentLoaded", function () {
    const form = document.getElementById("resignationForm");

    form.addEventListener("submit", function (e) {
        // Let browser show validation if fields are missing
        if (!form.checkValidity()) {
            return;
        }

        // Prevent form from submitting right away
        e.preventDefault();

        // Show confirmation popup
        document.getElementById("popup").style.display = "block";
        document.getElementById("overlay").style.display = "block";
    });
});

function confirmResignation() {
    const currentDate = new Date();
    const formattedResignationDate = currentDate.toISOString().split('T')[0];

    const lastWorkingDay = new Date();
    lastWorkingDay.setDate(currentDate.getDate() + 60);
    const formattedLastWorkingDay = lastWorkingDay.toISOString().split('T')[0];

    localStorage.setItem('resignationDate', formattedResignationDate);
    localStorage.setItem('lastWorkingDay', formattedLastWorkingDay);

    document.getElementById("resignationForm").submit(); // Now actually submit the form
}

function hidePopup() {
    document.getElementById("popup").style.display = "none";
    document.getElementById("overlay").style.display = "none";
}

window.onload = function () {
    const resignationDate = localStorage.getItem('resignationDate');
    const lastWorkingDay = localStorage.getItem('lastWorkingDay');

    if (resignationDate && document.getElementById('res_date')) {
        document.getElementById('res_date').value = resignationDate;
    }

    if (lastWorkingDay && document.getElementById('last_day')) {
        document.getElementById('last_day').value = lastWorkingDay;
    }
};
