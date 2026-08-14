// =========================================
// SHOW / HIDE PASSWORD
// =========================================

function togglePassword(inputId, button) {

    const input = document.getElementById(inputId);

    if (input.type === "password") {

        input.type = "text";

        button.textContent = "🙈";

    } else {

        input.type = "password";

        button.textContent = "👁";

    }
}


// =========================================
// PASSWORD VALIDATION
// =========================================

const passwordInput = document.getElementById("newPassword");

passwordInput.addEventListener("input", function () {

    const password = passwordInput.value;

    checkRequirement(
        "length",
        password.length >= 8
    );

    checkRequirement(
        "uppercase",
        /[A-Z]/.test(password)
    );

    checkRequirement(
        "number",
        /[0-9]/.test(password)
    );

    checkRequirement(
        "special",
        /[^A-Za-z0-9]/.test(password)
    );

});


function checkRequirement(id, valid) {

    const element = document.getElementById(id);

    const icon = element.querySelector("span");

    if (valid) {

        element.classList.add("valid");

        icon.textContent = "✓";

    } else {

        element.classList.remove("valid");

        icon.textContent = "○";

    }
}


// =========================================
// RESET PASSWORD
// =========================================

function resetPassword() {

    const password =
        document.getElementById("newPassword").value;

    const confirmPassword =
        document.getElementById("confirmPassword").value;


    if (password === "" || confirmPassword === "") {

        alert("Please enter your password.");

        return;
    }


    if (password !== confirmPassword) {

        alert("Passwords do not match.");

        return;
    }


    if (
        password.length < 8 ||
        !/[A-Z]/.test(password) ||
        !/[0-9]/.test(password) ||
        !/[^A-Za-z0-9]/.test(password)
    ) {

        alert("Please meet all password requirements.");

        return;
    }


    alert("Password reset successfully!");

}


// =========================================
// BACK
// =========================================

function goBack() {

    window.history.back();

}
function toggleRequirements() {

    const requirements =
        document.getElementById("requirements");

    requirements.classList.toggle("show");
}