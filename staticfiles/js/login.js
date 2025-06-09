if (localStorage.getItem("authToken")) {
        window.location.href = "dashboard.html";
      }

      function login() {
        const username = document.getElementById("username").value;
        const password = document.getElementById("password").value;

        if (username === "admin" && password === "password") {
          localStorage.setItem("authToken", "true");
          history.replaceState(null, "", "dashboard.html"); // Prevent back navigation
          window.location.href = "dashboard.html";
        } else {
          alert("Invalid credentials");
        }
      }
      function togglePassword(icon) {
        const passwordInput = document.getElementById("password");
        if (passwordInput.type === "password") {
          passwordInput.type = "text";
          icon.classList.remove("fa-eye-slash");
          icon.classList.add("fa-eye");
        } else {
          passwordInput.type = "password";
          icon.classList.remove("fa-eye");
          icon.classList.add("fa-eye-slash");
        }
      }



      // Prevent going back to logged-in page after logout
      //history.pushState(null, null, location.href);
      //window.onpopstate = function () {
      //history.go(1);
      //};