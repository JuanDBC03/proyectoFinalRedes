// Como Nginx es tu Gateway, esta es la ÚNICA URL que tu frontend necesita conocer
const BASE_URL = "http://localhost/api/v1";

// Función genérica para hacer peticiones seguras
async function peticionSegura(endpoint, opciones = {}) {
    // Sacamos el token que guardaste en el navegador al hacer login
    const token = localStorage.getItem("token_jwt");

    // Preparamos los Headers (inyectando el token si existe)
    const headers = {
        "Content-Type": "application/json",
        ...opciones.headers
    };

    if (token) {
        headers["Authorization"] = `Bearer ${token}`;
    }

    // Hacemos la petición a Nginx
    const respuesta = await fetch(`${BASE_URL}${endpoint}`, {
        ...opciones,
        headers
    });

    if (!respuesta.ok) {
        if (respuesta.status === 401) {
            alert("Tu sesión expiró. Vuelve a iniciar sesión.");
            window.location.href = "index.html"; // Lo mandas al login
        }
        const errorData = await respuesta.json();
        throw new Error(errorData.detail || "Error en la petición");
    }

    return await respuesta.json();
}

// 📬 👇 NUEVA FUNCIÓN: Obtener los correos limpios de MailHog
async function obtenerBuzonSimulado() {
    try {
        // Nginx redirigirá /notificaciones/buzon hacia tu notificaciones_service
        return await peticionSegura("/notificaciones/buzon", { method: "GET" });
    } catch (error) {
        console.error("⚠️ Error al cargar el buzón de correo:", error.message);
        return []; // Retornamos un array vacío preventivo para que no se rompa el renderizado
    }
}