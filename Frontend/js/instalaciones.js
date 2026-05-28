// js/instalaciones.js

async function cargarVistaInstalaciones() {
    document.getElementById("dinamicHeader").innerHTML = `<h1>Gestión de Instalaciones</h1><button class="btn-primary" onclick="abrirModalInstalacion()">➕ Nueva Instalación</button>`;
    const grid = document.getElementById("gridEventos");
    grid.innerHTML = "<p>Cargando registros de instalaciones...</p>";
    
    try {
        const resp = await fetch("http://localhost/api/v1/instalaciones/", { 
            headers: { "Authorization": `Bearer ${token}` } 
        });
        if(!resp.ok) throw new Error("Error obteniendo instalaciones");
        const instalaciones = await resp.json();
        
        grid.innerHTML = "";
        if(instalaciones.length === 0) {
            grid.innerHTML = "<p style='color: gray;'>No se han registrado instalaciones en el sistema aún.</p>";
            return;
        }

        instalaciones.forEach(i => {
            const id = i._id || i.id;
            const tipo = i.tipo || "Desconocido";
            const capacidad = i.capacidad || 0;
            const ubicacion = i.ubicacion || 'Sin definir';

            const tarjeta = document.createElement("div");
            tarjeta.className = "event-card";
            
            tarjeta.innerHTML = `
                <div class="event-icon">🏢</div>
                <h3 class="event-title" style="text-transform: capitalize;">${tipo}</h3>
                <p class="event-meta"><strong>ID:</strong> ${id}</p>
                <p class="event-meta"><strong>Capacidad:</strong> ${capacidad} personas</p>
                <p class="event-meta"><strong>Ubicación:</strong> ${ubicacion}</p>
                <div class="action-btns">
                    <button style="background-color:#0078d4;" onclick="abrirModalEditarInstalacion('${id}', '${tipo}', ${capacidad}, '${ubicacion}')">✏️ Editar</button>
                </div>
            `;
            grid.appendChild(tarjeta);
        });
    } catch(e) { 
        mostrarToast("El microservicio de instalaciones no respondió o está offline.", "error");
        grid.innerHTML = "<p style='color:red;'>El microservicio de instalaciones no respondió o está offline.</p>"; 
    }
}

// --- GESTIÓN DE MODALES ---

function abrirModalInstalacion() {
    document.getElementById("tituloModalInstalacion").innerText = "🏢 Nueva Instalación";
    document.getElementById("instIdOculto").value = "";
    
    const idVisible = document.getElementById("instIdVisible");
    idVisible.value = "";
    idVisible.disabled = false; 

    document.getElementById("instTipo").value = "salon";
    document.getElementById("instCapacidad").value = "";
    document.getElementById("instUbicacion").value = "";
    document.getElementById("modalInstalacion").style.display = "flex";
}

function abrirModalEditarInstalacion(id, tipo, cap, ubi) {
    document.getElementById("tituloModalInstalacion").innerText = "✏️ Editar Instalación";
    document.getElementById("instIdOculto").value = id;
    
    const idVisible = document.getElementById("instIdVisible");
    idVisible.value = id;
    idVisible.disabled = true;

    document.getElementById("instTipo").value = tipo;
    document.getElementById("instCapacidad").value = cap;
    document.getElementById("instUbicacion").value = ubi;
    document.getElementById("modalInstalacion").style.display = "flex";
}

function cerrarModalInstalacion() {
    document.getElementById("modalInstalacion").style.display = "none";
}

// --- GUARDAR EN BD ---

async function guardarInstalacionBD() {
    console.log("¡Botón Guardar clickeado!"); 

    try {
        const elIdVisible = document.getElementById("instIdVisible");
        const elTipo = document.getElementById("instTipo");
        const elCapacidad = document.getElementById("instCapacidad");
        const elUbicacion = document.getElementById("instUbicacion");

        // CAMBIO AQUÍ: Toast si el HTML no está completo
        if (!elIdVisible || !elCapacidad) {
            console.error("Faltan campos en el HTML. Asegúrate de haber actualizado el modal en dashboard.html.");
            return mostrarToast("Error crítico: El formulario HTML no está actualizado.", "error");
        }

        const idOculto = document.getElementById("instIdOculto").value;
        const idVisible = elIdVisible.value.trim();
        const tipo = elTipo.value;
        const capacidad = elCapacidad.value;
        const ubicacion = elUbicacion.value;

        // CAMBIO AQUÍ: Toast de validación de campos
        if (!idVisible || !capacidad || !ubicacion) {
            return mostrarToast("Por favor, completa el ID, la capacidad y la ubicación.", "warning");
        }

        const payload = {
            id: idVisible, 
            ubicacion: ubicacion,
            tipo: tipo,
            capacidad: parseInt(capacidad)
        };

        console.log("Enviando este payload al backend:", payload);

        const url = idOculto ? `http://localhost/api/v1/instalaciones/${idOculto}` : "http://localhost/api/v1/instalaciones/";
        const method = idOculto ? "PUT" : "POST";

        const respuesta = await fetch(url, {
            method: method,
            headers: { "Content-Type": "application/json", "Authorization": `Bearer ${token}` },
            body: JSON.stringify(payload)
        });

        // --- VALIDACIÓN BLINDADA ---
        if(!respuesta.ok) {
            let errorMsg = "Error desconocido del servidor.";
            try {
                const err = await respuesta.json();
                errorMsg = err.detail || JSON.stringify(err);
            } catch(e) {
                errorMsg = await respuesta.text(); 
            }
            console.error("El backend rechazó la petición:", errorMsg);
            
            // CAMBIO AQUÍ: Toast para error del backend
            return mostrarToast("Error al guardar: " + errorMsg, "error");
        }

        // CAMBIO AQUÍ: Éxito! Toast elegante 
        mostrarToast(`¡Instalación ${idOculto ? 'actualizada' : 'registrada'} exitosamente!`, "success");
        
        cerrarModalInstalacion();
        cargarVistaInstalaciones(); 

    } catch (error) {
        console.error("Error crítico en el JavaScript:", error);
        mostrarToast("Ocurrió un error de red inesperado.", "error");
    }
}