// js/evaluaciones.js

async function cargarVistaEvaluaciones() {
    document.getElementById("dinamicHeader").innerHTML = `<h1>Historial de Evaluaciones Académicas</h1>`;
    const grid = document.getElementById("gridEventos");
    grid.innerHTML = "<p>Cargando registros de evaluaciones...</p>";
    
    try {
        const resp = await fetch("http://localhost/api/v1/evaluaciones/", { headers: { "Authorization": `Bearer ${token}` } });
        if(!resp.ok) throw new Error("Error obteniendo evaluaciones");
        
        // Volvemos a la lectura plana del array
        const evaluaciones = await resp.json();
        
        grid.innerHTML = "";
        if(evaluaciones.length === 0) {
            grid.innerHTML = "<p style='color: gray;'>No se han registrado evaluaciones en el sistema aún.</p>";
            return;
        }

        evaluaciones.forEach(ev => {
            const fecha = ev.fechaEvaluacion ? new Date(ev.fechaEvaluacion).toLocaleString() : 'Sin fecha';
            const badgeClass = ev.estado === "aprobado" ? "status-aprobado" : "status-pendiente";
            
            let detalleHTML = "";
            if(ev.estado === "aprobado") {
                detalleHTML = `<strong>Acta Adjunta:</strong> ${ev.actaAprovacion || 'acta.pdf'}`;
            } else {
                detalleHTML = `<strong>Justificación:</strong> ${ev.justificacion || 'Sin observaciones.'}`;
            }

            const tarjeta = document.createElement("div");
            tarjeta.className = "event-card";
            tarjeta.innerHTML = `
                <div class="event-icon">📝</div>
                <h3 class="event-title">Dictamen Académico</h3>
                <p class="event-meta"><strong>ID Evento:</strong> ${ev.eventoId}</p>
                <p class="event-meta"><strong>Evaluador (ID):</strong> ${ev.usuarioId}</p>
                <p class="event-meta"><strong>Fecha:</strong> ${fecha}</p>
                <p class="event-meta" style="background: #f3f2f1; padding: 8px; border-radius: 4px; font-size: 13px; margin-top: 5px;">
                    ${detalleHTML}
                </p>
                <span class="status-badge ${badgeClass}">${ev.estado.toUpperCase()}</span>
            `;
            grid.appendChild(tarjeta);
        });

    } catch(e) { 
        grid.innerHTML = "<p style='color:red;'>El microservicio de evaluaciones no respondió o está offline.</p>"; 
    }
}

function abrirModalCrearEvaluacion(eventoId, estadoPreseleccionado) {
    document.getElementById("modalEvaluacionEvento").style.display = "flex";
    document.getElementById("evaluacionEventoId").value = eventoId;
    document.getElementById("evaluacionEstado").value = estadoPreseleccionado;
    
    document.getElementById("tituloModalEvaluacion").innerText = estadoPreseleccionado === 'aprobado' ? "✔️ Aprobar Evento" : "❌ Rechazar Evento";

    const divJustificacion = document.getElementById("divJustificacion");
    const divActa = document.getElementById("divActa");

    document.getElementById("evaluacionJustificacion").value = "";
    document.getElementById("evaluacionActa").value = "";

    if (estadoPreseleccionado === 'rechazado') {
        divJustificacion.style.display = "block";
        divActa.style.display = "none";
    } else {
        divJustificacion.style.display = "none";
        divActa.style.display = "block";
    }
}

function cerrarModalCrearEvaluacion() {
    document.getElementById("modalEvaluacionEvento").style.display = "none";
}

async function guardarEvaluacionBD() {
    const eventoId = document.getElementById("evaluacionEventoId").value;
    const estado = document.getElementById("evaluacionEstado").value;
    const justificacion = document.getElementById("evaluacionJustificacion").value;
    const acta = document.getElementById("evaluacionActa").value;

    if (estado === 'rechazado' && !justificacion.trim()) {
        return mostrarToast("Por favor, escriba la justificación académica del rechazo.", "warning");
    }
    if (estado === 'aprobado' && !acta.trim()) {
        return mostrarToast("Por favor, escriba el nombre del documento PDF (Acta de aprobación).", "warning");
    }

    const payloadDecodificado = JSON.parse(atob(token.split('.')[1]));
    const usuarioIdReal = parseInt(payloadDecodificado.sub || 0);

    const payloadEvaluacion = {
        estado: estado,
        fechaEvaluacion: new Date().toISOString(),
        justificacion: estado === 'rechazado' ? justificacion : "", 
        actaAprobacion: estado === 'aprobado' ? acta : "", 
        eventoId: eventoId.toString(),
        usuarioId: usuarioIdReal 
    };

    try {
        const respuesta = await fetch("http://localhost/api/v1/evaluaciones/", {
            method: "POST",
            headers: { "Content-Type": "application/json", "Authorization": `Bearer ${token}` },
            body: JSON.stringify(payloadEvaluacion)
        });

        if(!respuesta.ok) {
            const err = await respuesta.json();
            console.error("Detalle del error 422:", err);
            return mostrarToast("Error al registrar la evaluación.", "error");
        }

        await fetch(`http://localhost/api/v1/eventos/${eventoId}/estado`, {
            method: "PATCH",
            headers: { "Content-Type": "application/json", "Authorization": `Bearer ${token}` },
            body: JSON.stringify({ estado: estado })
        });

        mostrarToast(`¡Evento ${estado} exitosamente y evaluación asentada!`, "success");
        cerrarModalCrearEvaluacion();
        cargarVistaEventos(); 

    } catch(e) { 
        mostrarToast("Error de red comunicándose con los microservicios.", "error"); 
    }
}