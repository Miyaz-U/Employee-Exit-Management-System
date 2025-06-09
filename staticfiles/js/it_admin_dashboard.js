document.addEventListener("DOMContentLoaded", function () {
  const emailButtons = document.querySelectorAll("form.email_form button.btn");
  const systemButtons = document.querySelectorAll("form.system_form button.btn");

  function handleButtonClick(button) {
    const form = button.closest("form");
    if (!form) return;

    // Immediately disable the button visually
    button.innerText = "Disabled";
    button.style.backgroundColor = "#95a5a6";
    button.disabled = true;

    // Let the form submit naturally (no preventDefault)
    form.submit();
  }

  emailButtons.forEach(function (button) {
    button.addEventListener("click", function () {
      handleButtonClick(button);
    });
  });

  systemButtons.forEach(function (button) {
    button.addEventListener("click", function () {
      handleButtonClick(button);
    });
  });
});
