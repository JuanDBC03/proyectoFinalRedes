// js/usuarios.js

async function cargarVistaUsuarios() {
    document.getElementById("dinamicHeader").innerHTML = `<h1>Gestión de Usuarios</h1><button class="btn-primary" style="background-color:#107c10;" onclick="abrirModalUsuario()">➕ Nuevo Usuario</button>`;
    const grid = document.getElementById("gridEventos");
    grid.innerHTML = "<p>Cargando lista de usuarios...</p>";
    
    try {
        const resp = await fetch("http://localhost/api/v1/usuarios/", { headers: { "Authorization": `Bearer ${token}` } });
        if(!resp.ok) throw new Error("Error obteniendo usuarios");
        const usuarios = await resp.json();
        
        grid.innerHTML = "";
        usuarios.forEach(u => {
            const tarjeta = document.createElement("div");
            tarjeta.className = "event-card";
            
            const userId = u._id || u.id;
            const telf = (u.telefonos && u.telefonos.length > 0) ? u.telefonos[0] : '';
            
            tarjeta.innerHTML = `
                <div class="event-icon">👤</div>
                <h3 class="event-title">${u.nombre} ${u.apellidos || ''}</h3>
                <p class="event-meta">📧 ${u.email}</p>
                <p class="event-meta">📞 ${telf || 'Sin teléfono'}</p>
                <span class="status-badge status-aprobado">${u.vinculacion?.[0]?.rol?.toUpperCase() || 'N/A'}</span>
                
                <div class="action-btns" style="margin-top: 10px; display: flex; gap: 5px;">
                    <button style="background-color:#0078d4;" onclick="abrirModalEditarUsuario('${userId}', '${u.nombre}', '${u.apellidos || ''}', '${telf}')">✏️ Editar</button>
                    <button style="background-color:#d13438;" onclick="eliminarUsuarioBD('${userId}')">🗑️ Eliminar</button>
                </div>
            `;
            grid.appendChild(tarjeta);
        });
    } catch(e) { grid.innerHTML = "<p style='color:red;'>Error cargando usuarios.</p>"; }
}

function abrirModalUsuario() { 
    document.getElementById("modalCrearUsuario").style.display = "flex"; 
}

function cerrarModalUsuario() { 
    document.getElementById("modalCrearUsuario").style.display = "none"; 
    document.getElementById("nuevoId").value = "";
    document.getElementById("nuevoNombre").value = "";
    document.getElementById("nuevoApellidos").value = "";
    document.getElementById("nuevoEmail").value = "";
    document.getElementById("nuevoTelefono").value = "";
    document.getElementById("nuevaPassword").value = "";
    document.getElementById("nuevoRol").value = "";
    document.getElementById("divEntidadAcademica").style.display = "none";
}

function abrirModalEditarUsuario(id, nombre, apellidos, telefono) {
    document.getElementById("modalEditarUsuario").style.display = "flex";
    document.getElementById("editarUsuarioId").value = id;
    document.getElementById("editarNombre").value = nombre;
    document.getElementById("editarApellidos").value = apellidos;
    document.getElementById("editarTelefono").value = telefono;
}

function cerrarModalEditarUsuario() {
    document.getElementById("modalEditarUsuario").style.display = "none";
}

async function guardarEdicionUsuarioBD() {
    const id = document.getElementById("editarUsuarioId").value;
    const nombre = document.getElementById("editarNombre").value;
    const apellidos = document.getElementById("editarApellidos").value;
    const telefono = document.getElementById("editarTelefono").value;

    if(!nombre || !apellidos || !telefono) {
        return mostrarToast("Por favor, completa todos los campos del perfil.", "warning");
    }

    const payload = { nombre: nombre, apellidos: apellidos, telefonos: [telefono] };

    try {
        const respuesta = await fetch(`http://localhost/api/v1/usuarios/${id}`, {
            method: "PUT",
            headers: { "Content-Type": "application/json", "Authorization": `Bearer ${token}` },
            body: JSON.stringify(payload)
        });

        if(respuesta.ok) {
            mostrarToast("¡Perfil de usuario actualizado con éxito!", "success");
            cerrarModalEditarUsuario();
            cargarVistaUsuarios();
        } else {
            const err = await respuesta.json();
            mostrarToast("Error: " + (err.detail || "No se pudo actualizar el usuario."), "error");
        }
    } catch(e) { mostrarToast("Error de red al intentar actualizar el usuario.", "error"); }
}

async function eliminarUsuarioBD(id) {
    confirmarAccion("¿Estás seguro de eliminar este usuario?", async () => {
        try {
            const respuesta = await fetch(`http://localhost/api/v1/usuarios/${id}`, {
                method: "DELETE",
                headers: { "Authorization": `Bearer ${token}` }
            });

            if(respuesta.ok || respuesta.status === 204) {
                mostrarToast("¡Usuario eliminado correctamente!", "success");
                cargarVistaUsuarios();
            } else {
                mostrarToast("Hubo un problema al intentar eliminar el usuario.", "error");
            }
        } catch(e) { mostrarToast("Error de red al intentar eliminar al usuario.", "error"); }
    });
}

async function cambiarFormularioRol() {
    const rol_seleccionado = document.getElementById("nuevoRol").value;
    const divEntidad = document.getElementById("divEntidadAcademica");
    const labelEntidad = document.getElementById("labelEntidad");
    const selectEntidad = document.getElementById("nuevaEntidadId");

    if (!rol_seleccionado) {
        divEntidad.style.display = "none";
        return;
    }

    divEntidad.style.display = "block";
    selectEntidad.innerHTML = '<option value="">Cargando opciones...</option>';

    let endpoint = "";
    if (rol_seleccionado === "estudiante") { labelEntidad.innerText = "Programa Académico"; endpoint = "http://localhost/api/v1/programas/"; }
    else if (rol_seleccionado === "docente") { labelEntidad.innerText = "Unidad Académica"; endpoint = "http://localhost/api/v1/unidades/"; }
    else if (rol_seleccionado === "secretariaAcademica") { labelEntidad.innerText = "Facultad"; endpoint = "http://localhost/api/v1/facultades/"; }

    try {
        const resp = await fetch(endpoint, { headers: { "Authorization": `Bearer ${token}` } });
        if (!resp.ok) throw new Error("Microservicio no disponible");
        
        const datos = await resp.json();
        selectEntidad.innerHTML = '<option value="">Seleccione una opción...</option>';
        datos.forEach(item => {
            const id = item._id || item.id;
            const nombre = item.nombre || "Opción sin nombre";
            selectEntidad.innerHTML += `<option value="${id}">${nombre}</option>`;
        });
    } catch (error) {
        console.warn("Usando datos de prueba (Mock)");
        if (rol_seleccionado === "estudiante") {
            selectEntidad.innerHTML = `<option value="60a7b05f9d2a4e2f9c8d5e1a">Ingeniería de Sistemas (Prueba)</option>`;
        } else if (rol_seleccionado === "docente") {
            selectEntidad.innerHTML = `<option value="60a7b05f9d2a4e2f9c8d5e2a">Unidad de Ciencias Básicas (Prueba)</option>`;
        } else if (rol_seleccionado === "secretariaAcademica") {
            selectEntidad.innerHTML = `<option value="60a7b05f9d2a4e2f9c8d5e3a">Facultad de Ingeniería (Prueba)</option>`;
        }
    }
}

async function guardarUsuarioBD() {
    const id_usuario = parseInt(document.getElementById("nuevoId").value);
    const nombre = document.getElementById("nuevoNombre").value;
    const apellidos = document.getElementById("nuevoApellidos").value;
    const email = document.getElementById("nuevoEmail").value;
    const telefono = document.getElementById("nuevoTelefono").value;
    const password = document.getElementById("nuevaPassword").value;
    const rol_usuario = document.getElementById("nuevoRol").value;
    const entidad_id = document.getElementById("nuevaEntidadId").value;

    if(!id_usuario || !nombre || !apellidos || !email || !telefono || !password || !rol_usuario || !entidad_id) {
        return mostrarToast("Por favor, completa todos los campos.", "warning");
    }

    const payloadDecodificado = JSON.parse(atob(token.split('.')[1]));
    const creadorIdReal = parseInt(payloadDecodificado.sub || 0);

    const payload = {
        id: id_usuario, nombre: nombre, apellidos: apellidos, email: email, telefono: telefono, password: password, rol: rol_usuario, entidad_id: entidad_id
    };

    try {
        const respuesta = await fetch(`http://localhost/api/v1/usuarios/?creador_id=${creadorIdReal}`, {
            method: "POST",
            headers: { "Content-Type": "application/json", "Authorization": `Bearer ${token}` },
            body: JSON.stringify(payload)
        });

        if(respuesta.ok) { 
            mostrarToast("¡Usuario creado con éxito!", "success"); 
            cerrarModalUsuario(); 
            cargarVistaUsuarios(); 
        } 
        else { 
            const err = await respuesta.json(); 
            mostrarToast("Error: " + (err.detail || "No se pudo guardar"), "error"); 
        }
    } catch(e) { mostrarToast("Error de red.", "error"); }
}