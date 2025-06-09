document.addEventListener("DOMContentLoaded", function () {
    const form = document.getElementById("feedbackForm");

    if (form) {
        form.addEventListener("submit", function (event) {
            event.preventDefault();

            const formData = new FormData(form);

            fetch(form.action, {
                method: "POST",
                body: formData,
                credentials: "same-origin",
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    alert(data.message);
                    window.location.href = data.redirect_url;
                } else {
                    alert("There was an error submitting the form.");
                }
            })
            .catch(error => {
                console.error("Error:", error);
                alert("Something went wrong. Please try again later.");
            });
        });
    }
});
