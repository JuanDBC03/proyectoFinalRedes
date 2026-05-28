// js/core.js

const token = localStorage.getItem("token_jwt");
const rol = localStorage.getItem("usuario_rol");

if (!token || !rol) window.location.href = "index.html";
document.getElementById("userEmail").innerText = `Perfil: ${rol}`;

function cerrarSesion() {
    localStorage.removeItem("token_jwt");
    localStorage.removeItem("usuario_rol");
    window.location.href = "index.html";
}

function configurarInterfaz() {
    const sidebar = document.getElementById("dinamicSidebar");
    let enlaces = ""; 

    if (rol === "docente") {
        enlaces += `<a href="#" id="nav-eventos" class="nav-item active" onclick="cambiarVista('eventos')">📁 Mis Eventos</a>`;
    } else if (rol === "secretariaAcademica") {
        enlaces += `
            <a href="#" id="nav-eventos" class="nav-item active" onclick="cambiarVista('eventos')">📁 Todos los Eventos</a>
            <a href="#" id="nav-instalaciones" class="nav-item" onclick="cambiarVista('instalaciones')">🏢 Instalaciones</a>
            <a href="#" id="nav-usuarios" class="nav-item" onclick="cambiarVista('usuarios')">👥 Gestión de Usuarios</a>
        `;
    } else if (rol === "estudiante") {
        enlaces += `
            <a href="#" id="nav-eventos" class="nav-item active" onclick="cambiarVista('eventos')">📅 Eventos Disponibles</a>
            <a href="#" id="nav-inscripciones" class="nav-item" onclick="cambiarVista('inscripciones')">✅ Mis Inscripciones</a>
        `;
    }

    enlaces += `<a href="#" id="nav-notificaciones" class="nav-item" onclick="cambiarVista('notificaciones')">📬 Buzón de Correos</a>`;

    sidebar.innerHTML = enlaces;
}

function cambiarVista(vista) {
    document.querySelectorAll('.nav-item').forEach(el => el.classList.remove('active'));
    const linkActivo = document.getElementById(`nav-${vista}`);
    if (linkActivo) linkActivo.classList.add('active');

    const grid = document.getElementById("gridEventos");
    if (grid) {
        grid.style.display = ""; 
        grid.style.flexDirection = "";
        grid.style.gap = "";
    }

    if (vista === 'eventos') {
        cargarVistaEventos();
    } else if (vista === 'usuarios') {
        cargarVistaUsuarios();
    } else if (vista === 'instalaciones') {
        cargarVistaInstalaciones();
    } else if (vista === 'inscripciones') {
        cargarVistaMisInscripciones();
    } else if (vista === 'notificaciones') {
        cargarVistaNotificaciones();
    } else if (vista === 'analytics') {
        if(typeof cargarVistaAnalytics === 'function') cargarVistaAnalytics();
    }
}

// Búsqueda global (filtrado de tarjetas en el DOM actual)
function filtrarContenido() {
    const searchInput = document.getElementById("searchInput");
    if (!searchInput) return;

    // Normalizar query: minúsculas y sin tildes/acentos
    const query = searchInput.value.toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "");

    // Filtramos tarjetas de eventos
    document.querySelectorAll(".event-card").forEach(card => {
        const text = (card.textContent || "").toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "");
        card.style.display = text.includes(query) ? "" : "none";
    });

    // Filtramos filas de tablas (usuarios, instalaciones)
    document.querySelectorAll("tbody tr").forEach(tr => {
        const text = (tr.textContent || "").toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "");
        tr.style.display = text.includes(query) ? "" : "none";
    });
}

// Arranque seguro cuando el DOM esté listo
window.onload = () => {
    configurarInterfaz();
    cambiarVista('eventos');
};


function mostrarToast(mensaje, tipo = 'success') {
    const container = document.getElementById('toast-container');
    if (!container) return;

    const toast = document.createElement('div');
    toast.className = `toast ${tipo}`;

    let icono = 'fa-check-circle';
    if (tipo === 'error') icono = 'fa-times-circle';
    if (tipo === 'warning') icono = 'fa-exclamation-triangle';

    toast.innerHTML = `<i class="fas ${icono}"></i> <span>${mensaje}</span>`;
    container.appendChild(toast);

    setTimeout(() => toast.classList.add('show'), 10);

    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => toast.remove(), 300);
    }, 3500);
}



let accionConfirmadaCallback = null;

function confirmarAccion(mensaje, callback) {
    document.getElementById('textoConfirmacion').textContent = mensaje;
    document.getElementById('modalConfirmacion').style.display = 'flex';
    accionConfirmadaCallback = callback;
}

function cerrarConfirmacion() {
    document.getElementById('modalConfirmacion').style.display = 'none';
    accionConfirmadaCallback = null;
}

// Escuchar el clic del botón rojo del modal de confirmación
document.getElementById('btnConfirmarAccion').addEventListener('click', () => {
    if (accionConfirmadaCallback) {
        accionConfirmadaCallback(); 
    }
    cerrarConfirmacion();
});