// js/eventos.js

function cargarVistaEventos() {
    const header = document.getElementById("dinamicHeader");
    if (rol === "docente") {
        header.innerHTML = `<h1>Mis Eventos</h1><button class="btn-primary" onclick="abrirModalCrearEvento()">➕ Nuevo Evento</button>`;
        cargarEventosBD('todos'); 
    } else if (rol === "secretariaAcademica") {
        header.innerHTML = `<h1>Lista de Eventos</h1>`;
        cargarEventosBD('todos');
    } else {
        header.innerHTML = `<h1>Eventos Pendientes</h1>`;
        cargarEventosBD('disponibles');
    }
}

async function cargarEventosBD(filtro) {
    const grid = document.getElementById("gridEventos");
    grid.innerHTML = "<p>Cargando eventos...</p>"; 
    try {
        const resp = await fetch(`http://localhost/api/v1/eventos/`, { headers: { "Authorization": `Bearer ${token}` } });
        
        // Volvemos a la lectura plana del array
        const eventos = await resp.json();
        
        grid.innerHTML = "";

        const hoy = new Date();
        const eventosFiltrados = eventos.filter(e => {
            if (filtro !== 'disponibles') return true;
            const fecha = new Date(e.realizacion?.fecha || e.fecha || 0);
            const estado = (e.estado || "").toLowerCase();
            return (fecha > hoy) && (estado === "aprobado" || estado === "aprovado");
        });

        if(eventosFiltrados.length === 0) {
            grid.innerHTML = "<p>No hay eventos visibles en esta sección con tu filtro actual.</p>";
            return;
        }

        eventosFiltrados.forEach(evento => {
            const id = evento._id || evento.id;
            const estado = (evento.estado || "pendiente").toLowerCase();
            let btns = "";
            
            if (rol === "docente") {
                btns = `<button style="background-color:#5c2d91;" onclick="abrirModalParticipantes('${id}')">👥 Participantes</button>
                        <button style="background-color:#d13438;" onclick="eliminarEvento('${id}')">🗑️</button>
                        <button style="background-color:#0078d4;" onclick="abrirModalEditarEvento('${id}')">✏️</button>`;
            } else if (rol === "secretariaAcademica") {
                if (estado !== "aprobado" && estado !== "rechazado") {
                    btns = `<button style="background-color:#107c10;" onclick="abrirModalCrearEvaluacion('${id}', 'aprobado')">✔️ Aprobar</button>
                            <button style="background-color:#d13438;" onclick="abrirModalCrearEvaluacion('${id}', 'rechazado')">❌ Rechazar</button>`;
                } else btns = `<span style="font-size:12px; color:gray;">Evaluado (${estado.toUpperCase()})</span>`;
            } else if (rol === "estudiante") {
                const creadorId = evento.creadoPor || (evento.organizador && evento.organizador[0] ? evento.organizador[0].usuarioId : 0);
                btns = `<button style="background-color:#107c10;" onclick="inscribirseEvento('${id}', '${evento.nombre}', '${creadorId}')">✋ Inscribirme</button>`;
            }

            const badgeClass = estado.includes("aprob") ? "status-aprobado" : "status-pendiente";
            const ubi = evento.realizacion?.instalaciones?.[0]?.instalacionId || 'Por definir';

            const card = document.createElement("div");
            card.className = "event-card";
            card.innerHTML = `<div class="event-icon">📄</div><h3 class="event-title">${evento.nombre}</h3>
                            <p class="event-meta">📍 ${ubi} | 👥 ${evento.cupoMaximo}</p>
                            <span class="status-badge ${badgeClass}">${estado.toUpperCase()}</span>
                            <div class="action-btns">${btns}</div>`;
            grid.appendChild(card);
        });

    } catch(e) { 
        mostrarToast("Error al cargar la lista de eventos.", "error"); 
        grid.innerHTML = "<p style='color:red;'>Error al cargar eventos.</p>"; 
    }
}

async function actualizarInstalacionesDisponibles() {
    const fecha = document.getElementById("eventoFecha").value;
    const horaInicio = document.getElementById("eventoHoraInicio").value;
    const horaFin = document.getElementById("eventoHoraFin").value;
    const cupos = parseInt(document.getElementById("eventoCupos").value) || 0;
    const select = document.getElementById("eventoUbicacion");

    if (!fecha || !horaInicio || !horaFin || cupos <= 0) {
        select.innerHTML = '<option value="">Ingrese fecha, horas y cupos...</option>';
        return;
    }

    select.innerHTML = '<option value="">Buscando disponibilidad...</option>';

    try {
        const fechaISO = new Date(fecha + "T00:00:00").toISOString();
        const url = `http://localhost/api/v1/eventos/instalaciones/disponibles?fecha=${fechaISO}&hora_inicio=${horaInicio}&hora_fin=${horaFin}&cupo_requerido=${cupos}`;
        const resp = await fetch(url, { headers: { "Authorization": `Bearer ${token}` } });
        const instalaciones = await resp.json();
        
        if (instalaciones.length === 0) { select.innerHTML = '<option value="">Ninguna instalación disponible</option>'; return; }

        select.innerHTML = '<option value="">Seleccione una instalación...</option>';
        instalaciones.forEach(inst => {
            const id = inst._id || inst.id;
            const option = document.createElement("option");
            option.value = id;
            option.setAttribute("data-capacidad", inst.capacidad || 30);
            option.innerText = `${inst.nombre || id} (Cap: ${inst.capacidad || 30})`;
            select.appendChild(option);
        });
    } catch (e) { 
        select.innerHTML = '<option value="">Error al cargar instalaciones</option>'; 
        mostrarToast("Fallo conectando al servicio de instalaciones", "warning"); 
    }
}

async function cargarOrganizacionesParaSelect() {
    const select = document.getElementById("eventoOrganizacion");
    select.innerHTML = '<option value="">Cargando organizaciones...</option>';
    try {
        const resp = await fetch("http://localhost/api/v1/organizaciones/", { headers: { "Authorization": `Bearer ${token}` } });
        const organizaciones = await resp.json();
        select.innerHTML = '<option value="">Sin organización externa</option>';
        organizaciones.forEach(org => {
            const option = document.createElement("option");
            option.value = org._id || org.id; option.innerText = org.nombre || "Org"; select.appendChild(option);
        });
    } catch (e) {
        select.innerHTML = `<option value="">Sin organización externa</option><option value="mock1">Alianza Tecnológica</option>`;
    }
}

async function abrirModalCrearEvento() {
    document.getElementById("tituloModalEvento").innerText = "➕ Crear Nuevo Evento";
    document.getElementById("eventoIdOculto").value = "";
    document.getElementById("eventoNombre").value = "";
    document.getElementById("eventoCupos").value = "";
    document.getElementById("eventoFecha").value = "";
    document.getElementById("modalEvento").style.display = "flex";
    await cargarOrganizacionesParaSelect();
}

async function abrirModalEditarEvento(id) {
    document.getElementById("tituloModalEvento").innerText = "✏️ Editar Evento";
    document.getElementById("eventoIdOculto").value = id;
    document.getElementById("modalEvento").style.display = "flex";
    await cargarOrganizacionesParaSelect();

    try {
        const resp = await fetch(`http://localhost/api/v1/eventos/${id}`, { headers: { "Authorization": `Bearer ${token}` } });
        if(resp.ok) {
            const evento = await resp.json();
            document.getElementById("eventoNombre").value = evento.nombre || "";
            document.getElementById("eventoCupos").value = evento.cupoMaximo || 0;
            if(evento.realizacion?.fecha) document.getElementById("eventoFecha").value = evento.realizacion.fecha.split('T')[0];
            await actualizarInstalacionesDisponibles();
        }
    } catch(e) { console.error(e); }
}

function cerrarModalEvento() { document.getElementById("modalEvento").style.display = "none"; }

async function guardarEventoBD() {
    const id = document.getElementById("eventoIdOculto").value;
    const payloadDecodificado = JSON.parse(atob(token.split('.')[1]));
    const usuarioIdReal = parseInt(payloadDecodificado.sub || 0);

    const instalacionId = document.getElementById("eventoUbicacion").value;
    
    if(!document.getElementById("eventoNombre").value || !instalacionId || !document.getElementById("eventoFecha").value) {
        return mostrarToast("Complete los campos obligatorios.", "warning");
    }

    const payload = {
        nombre: document.getElementById("eventoNombre").value,
        estado: "registrado", tipo: document.getElementById("eventoTipo").value,
        realizacion: {
            instalaciones: [{ instalacionId: instalacionId, capacidadInstalacion: 30 }],
            fecha: new Date(document.getElementById("eventoFecha").value + "T00:00:00").toISOString(),
            horaInicio: document.getElementById("eventoHoraInicio").value,
            horaFin: document.getElementById("eventoHoraFin").value
        },
        organizador: [{ usuarioId: usuarioIdReal, avalPDF: "", tipoAval: document.getElementById("eventoTipoAval").value, tipo: "principal" }],
        organizacion: [], capacidad: 30, creadoPor: usuarioIdReal, 
        cupoMaximo: parseInt(document.getElementById("eventoCupos").value) || 30, participantes: []
    };

    const url = id ? `http://localhost/api/v1/eventos/${id}` : `http://localhost/api/v1/eventos/`;
    try {
        const resp = await fetch(url, { method: id ? "PUT" : "POST", headers: { "Content-Type": "application/json", "Authorization": `Bearer ${token}` }, body: JSON.stringify(payload) });
        
        if(resp.ok) { 
            mostrarToast("¡Evento guardado exitosamente!", "success"); 
            cerrarModalEvento(); 
            cargarVistaEventos(); 
        } else {
            mostrarToast("Error al guardar el evento en la base de datos.", "error");
        }
    } catch(e) { 
        mostrarToast("Error de red. No se pudo contactar al servidor.", "error"); 
    }
}

async function eliminarEvento(id) {
    confirmarAccion("¿Estás seguro de que deseas eliminar permanentemente este evento? Esta acción no se puede deshacer.", async () => {
        try { 
            const resp = await fetch(`http://localhost/api/v1/eventos/${id}`, { method: 'DELETE', headers: { "Authorization": `Bearer ${token}` } }); 
            if(resp.ok) {
                mostrarToast("Evento eliminado correctamente.", "success");
                cargarVistaEventos(); 
            } else {
                mostrarToast("No se pudo eliminar el evento.", "error");
            }
        } catch(e) { 
            console.error(e); 
            mostrarToast("Error de conexión al intentar eliminar.", "error");
        }
    });
}

async function abrirModalParticipantes(id) {
    document.getElementById("modalParticipantes").style.display = "flex";
    const divLista = document.getElementById("listaParticipantes");
    
    divLista.innerHTML = "<p style='color: gray; font-style: italic;'>Cargando lista y buscando nombres...</p>";

    try {
        const resp = await fetch(`http://localhost/api/v1/eventos/${id}`, { headers: { "Authorization": `Bearer ${token}` } });
        if(resp.ok) {
            const evento = await resp.json();
            
            if(!evento.participantes || evento.participantes.length === 0) {
                return divLista.innerHTML = "<p>Aún no hay inscritos en este evento.</p>";
            }

            let html = '<ul style="list-style: none; padding: 0;">';
            
            const promesasParticipantes = evento.participantes.map(async (p) => {
                let nombreEstudiante = "Usuario Desconocido";
                
                try {
                    const respUser = await fetch(`http://localhost/api/v1/usuarios/${p.usuarioId}`, {
                        headers: { "Authorization": `Bearer ${token}` }
                    });
                    
                    if (respUser.ok) {
                        const userDatos = await respUser.json();
                        nombreEstudiante = userDatos.nombre || userDatos.nombreCompleto || `Estudiante ${p.usuarioId}`;
                    }
                } catch (err) {
                    console.error(`Fallo al obtener nombre del ID ${p.usuarioId}`, err);
                }
                
                return `<li style="padding: 12px 10px; border-bottom: 1px solid #eee; display: flex; justify-content: space-between; align-items: center;">
                            <span>👤 <strong>${nombreEstudiante}</strong> <small style="color:#888;">(ID: ${p.usuarioId})</small></span>
                            <span style="font-size: 11px; font-weight: bold; color: #5c2d91; background: #f3e9fa; padding: 4px 10px; border-radius: 12px;">
                                ${p.estado.toUpperCase()}
                            </span>
                        </li>`;
            });

            const itemsHtml = await Promise.all(promesasParticipantes);
            html += itemsHtml.join('');
            
            divLista.innerHTML = html + '</ul>';
        } else {
            divLista.innerHTML = "<p style='color: red;'>No se pudo obtener la información del evento.</p>";
        }
    } catch(e) { 
        console.error("Error cargando participantes:", e);
        divLista.innerHTML = "<p style='color: red;'>Error de conexión al cargar la lista.</p>"; 
    }
}

function cerrarModalParticipantes() { document.getElementById("modalParticipantes").style.display = "none"; }

document.addEventListener('DOMContentLoaded', () => {
    document.getElementById("eventoFecha")?.addEventListener("change", actualizarInstalacionesDisponibles);
    document.getElementById("eventoHoraInicio")?.addEventListener("change", actualizarInstalacionesDisponibles);
    document.getElementById("eventoHoraFin")?.addEventListener("change", actualizarInstalacionesDisponibles);
    document.getElementById("eventoCupos")?.addEventListener("input", actualizarInstalacionesDisponibles);
});