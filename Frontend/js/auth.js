async function iniciarSesion(email, password) {
    try {
        const respuesta = await peticionSegura("/auth/login", {
            method: "POST",
            body: JSON.stringify({ email, password })
        });

        localStorage.setItem("token_jwt", respuesta.access_token);
        mostrarToast("¡Login exitoso!", "success");
        
        // Damos un respiro mínimo de 1 segundo para que el usuario vea el toast verde antes de saltar
        setTimeout(() => {
            window.location.href = "dashboard.html";
        }, 1000);
        
    } catch (error) {
        console.error(error);
        mostrarToast(error.message || "Error al iniciar sesión", "error");
    }
}