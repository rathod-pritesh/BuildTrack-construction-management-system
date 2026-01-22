document.addEventListener("DOMContentLoaded", function () {
    // Toggle Password Visibility
    document.querySelectorAll(".toggle-password").forEach(icon => {
        icon.addEventListener("click", function () {
            const input = this.previousElementSibling;
            if (input.type === "password") {
                input.type = "text";
                this.classList.replace("fa-eye-slash", "fa-eye");
            } else {
                input.type = "password";
                this.classList.replace("fa-eye", "fa-eye-slash");
            }
        });
    });

    // Add Event Listener Safely
    function safeEventListener(id, event, callback) {
        const element = document.getElementById(id);
        if (element) {
            element.addEventListener(event, callback);
        }
    }

    // Handle Login & Register Modal Switching
    safeEventListener("registerRedirect", "click", function () {
        const loginModal = bootstrap.Modal.getInstance(document.getElementById("loginModal"));
        if (loginModal) loginModal.hide();
        new bootstrap.Modal(document.getElementById("registerModal")).show();
    });

    safeEventListener("loginRedirect", "click", function () {
        const registerModal = bootstrap.Modal.getInstance(document.getElementById("registerModal"));
        if (registerModal) registerModal.hide();
        new bootstrap.Modal(document.getElementById("loginModal")).show();
    });

    // Show Login & Register Modals on Button Click
    safeEventListener("loginBtn", "click", function () {
        new bootstrap.Modal(document.getElementById("loginModal")).show();
    });

    safeEventListener("registerBtn", "click", function () {
        new bootstrap.Modal(document.getElementById("registerModal")).show();
    });

    // Forgot Password Alert
    safeEventListener("forgotPassword", "click", function () {
        alert("A password reset link has been sent to your email.");
    });

    // Navigation Auto-Loading
    document.querySelectorAll(".nav-link").forEach(link => {
        link.addEventListener("click", (e) => {
            // Close navbar if open on mobile
            const navbarCollapse = document.getElementById("navbarNav");
            if (navbarCollapse && navbarCollapse.classList.contains("show")) {
                const bsCollapse = bootstrap.Collapse.getInstance(navbarCollapse);
                if (bsCollapse) bsCollapse.hide();
            }

            // Get the target URL from the link's href attribute
            const targetUrl = link.getAttribute("href");

            // Navigate to the target URL
            if (targetUrl) {
                window.location.href = targetUrl;
            }
        });
    });

    // Footer Navigation Links
    document.querySelectorAll(".footer-links a").forEach(link => {
        link.addEventListener("click", (e) => {
            e.preventDefault();

            // Get the target URL from the link's href attribute
            const targetUrl = link.getAttribute("href");

            // Navigate to the target URL
            if (targetUrl) {
                window.location.href = targetUrl;
            }
        });
    });

    // Login Form Validation
    const loginForm = document.querySelector('form[action*="login"]');
    if (loginForm) {
        loginForm.addEventListener('submit', function(e) {
            const email = this.querySelector('input[name="email"]').value;
            const password = this.querySelector('input[name="password"]').value;
            
            if (!email || !password) {
                e.preventDefault();
                showToast("Please fill in all fields", "bg-danger");
                return false;
            }
            
            if (!validateEmail(email)) {
                e.preventDefault();
                showToast("Please enter a valid email address", "bg-danger");
                return false;
            }
        });
    }

    const registerForm = document.getElementById('registerForm');
if (registerForm) {
    registerForm.addEventListener('submit', function(e) {
        const username = this.querySelector('input[name="username"]').value;
        const email = this.querySelector('input[name="email"]').value;
        const password = this.querySelector('input[name="password"]').value;
        const confirmPassword = this.querySelector('input[name="confirmpassword"]').value;

        if (!username || !email || !password || !confirmPassword) {
            e.preventDefault();
            showToast("Please fill in all fields", "bg-danger");
            return false;
        }

        if (!validateEmail(email)) {
            e.preventDefault();
            showToast("Please enter a valid email address", "bg-danger");
            return false;
        }

        if (password.length < 8) {
            e.preventDefault();
            showToast("Password must be at least 8 characters long", "bg-danger");
            return false;
        }

        if (!/\d/.test(password)) {
            e.preventDefault();
            showToast("Password must contain at least one number", "bg-danger");
            return false;
        }

        if (!/[a-zA-Z]/.test(password)) {
            e.preventDefault();
            showToast("Password must contain at least one letter", "bg-danger");
            return false;
        }

        if (!/[!@#$%^&*]/.test(password)) {
            e.preventDefault();
            showToast("Password must contain at least one special character", "bg-danger");
            return false;
        }

        if (password !== confirmPassword) {
            e.preventDefault();
            showToast("Passwords do not match", "bg-danger");
            return false;
        }

        showToast("Waiting for admin approval", "bg-info");
    });
}


    // Email validation function
    function validateEmail(email) {
        const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return re.test(email);
    }

    // Auto-hide alerts after 5 seconds
    setTimeout(function() {
        document.querySelectorAll('.alert').forEach(function(alert) {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        });
    }, 5000);

    // Toast Notification Function
    function showToast(message, bgColor = "bg-primary") {
        const toastEl = document.getElementById("toast");
        const toastBody = document.querySelector(".toast-body");
        if (toastEl && toastBody) {
            toastBody.textContent = message;
            toastEl.classList.remove("bg-primary", "bg-success", "bg-danger", "bg-warning", "bg-info");
            toastEl.classList.add(bgColor);
            const toast = new bootstrap.Toast(toastEl);
            toast.show();
        }
    }



    // Login Form Handling
    safeEventListener("loginForm", "submit", function (e) {
        e.preventDefault();
        const email = document.getElementById("loginEmail")?.value;
        const password = document.getElementById("loginPassword")?.value;
        
        if (!email || !password) {
            showToast("Please fill in all fields", "bg-danger");
            return;
        }
        
        if (!validateEmail(email)) {
            showToast("Please enter a valid email address", "bg-danger");
            return;
        }
        
        showToast("Login successful!", "bg-success");
        this.submit();
    });

    const flashMessages = document.querySelectorAll('.alert');
    if (flashMessages.length > 0) {
        // Auto-hide alerts after 5 seconds
        setTimeout(function() {
            flashMessages.forEach(function(alert) {
                const bsAlert = new bootstrap.Alert(alert);
                bsAlert.close();
            });
        }, 5000);
    }

    // Handle logout confirmation
    const logoutButtons = document.querySelectorAll('a[href*="logout"]');
    logoutButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            if (!confirm('Are you sure you want to logout?')) {
                e.preventDefault();
            }
        });
    });

    // Display session timeout warning
    let sessionTimeout;
    function resetSessionTimeout() {
        clearTimeout(sessionTimeout);
        sessionTimeout = setTimeout(function() {
            showToast("Your session will expire in 1 minute due to inactivity.", "bg-warning");
        }, 14 * 60 * 1000); // 14 minutes (assuming 15 minute session timeout)
    }

    // Reset session timeout on user activity
    ['click', 'keypress', 'scroll', 'mousemove'].forEach(function(event) {
        document.addEventListener(event, resetSessionTimeout);
    });
    
    // Initialize session timeout
    resetSessionTimeout();
});

document.addEventListener("DOMContentLoaded", function () {
    const navLinks = document.querySelectorAll(".nav-link");
    navLinks.forEach((link) => {
      link.addEventListener("mouseover", function () {
        link.classList.add("hover-effect");
      });
      link.addEventListener("mouseleave", function () {
        link.classList.remove("hover-effect");
      });
    });
  
    // Smooth transition for login/register forms
    const loginForm = document.getElementById("loginForm");
    const registerForm = document.getElementById("registerForm");
    if (loginForm) loginForm.style.animation = "fadeIn 0.5s ease-in-out";
    if (registerForm) registerForm.style.animation = "fadeIn 0.5s ease-in-out";
  });
  
  