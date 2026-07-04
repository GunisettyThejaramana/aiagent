document
.getElementById("loginBtn")
.addEventListener("click", login);

async function login() {

    const username =
        document.getElementById("username").value;

    const password =
        document.getElementById("password").value;

    const formData =
        new URLSearchParams();

    formData.append(
        "username",
        username
    );

    formData.append(
        "password",
        password
    );

    try {

        const response =
            await fetch("/auth/login", {

                method: "POST",

                headers: {
                    "Content-Type":
                    "application/x-www-form-urlencoded"
                },

                body: formData
            });

        const data =
            await response.json();

        if (!response.ok) {

            document
            .getElementById("message")
            .innerText =
                data.detail;

            return;
        }

        localStorage.setItem(
            "token",
            data.access_token
        );

        window.location.href =
            "/dashboard";

    } catch (error) {

        console.error(error);

        document
        .getElementById("message")
        .innerText =
            "Login failed";
    }
}