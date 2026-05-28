// ==========================================================
// LÓGICA DE INSCRripciones (js/inscripciones.js)
// ==========================================================

async function inscribirseEvento(eventoId, eventoTitulo, docenteId) {
    try {
        const resp = await fetch("http://localhost/api/v1/eventos/inscripciones/", {
            method: "POST",
            headers: { 
                "Content-Type": "application/json",
                "Authorization": `Bearer ${token}` 
            },
            body: JSON.stringify({
                evento_id: eventoId,
                evento_titulo: eventoTitulo
            })
        });

        if (resp.ok) {
            mostrarToast(`¡Te has inscrito exitosamente al evento: ${eventoTitulo}!`, "success");
            
            // 👇 DISPARAMOS LA NOTIFICACIÓN SIMULADA AL DOCENTE
            if (docenteId && docenteId !== '0' && docenteId !== 0) {
                await generarNotificacionInscripcion(docenteId, eventoTitulo);
            }
        } else {
            const err = await resp.json();
            mostrarToast("No se pudo realizar la inscripción: " + (err.detail || "Error desconocido"), "error");
        }
    } catch(e) {
        console.error("Error en la petición de inscripción:", e);
        mostrarToast("Error de red conectando con el servidor de inscripciones.", "error");
    }
}

async function generarNotificacionInscripcion(docenteId, eventoTitulo) {
    try {
        const payloadDecodificado = JSON.parse(atob(token.split('.')[1]));
        const miId = parseInt(payloadDecodificado.sub || 0);

        // Buscar nombre del estudiante
        let nombreEstudiante = `ID ${miId}`;
        try {
            const respUser = await fetch(`http://localhost/api/v1/usuarios/${miId}`, {
                headers: { "Authorization": `Bearer ${token}` }
            });
            if (respUser.ok) {
                const userDatos = await respUser.json();
                nombreEstudiante = `${userDatos.nombre} ${userDatos.apellidos || ''}`.trim();
            }
        } catch(e) {} // Ignorar fallo silencioso

        // Guardar la notificación
        const nuevaNotificacion = {
            idUnico: "insc_" + Date.now(),
            destinatarioId: parseInt(docenteId), // Para que solo la vea el profe
            remitente: "Sistema de Inscripciones",
            asunto: `INSCRIPCIÓN: Nuevo estudiante en ${eventoTitulo}`,
            cuerpo: `El/la estudiante <strong>${nombreEstudiante}</strong> ha registrado su participación en tu evento académico. Puedes revisar la lista completa de participantes en el módulo de eventos.`,
            fecha: new Date().toISOString()
        };

        let buzon = JSON.parse(localStorage.getItem("notificaciones_simuladas")) || [];
        buzon.push(nuevaNotificacion);
        localStorage.setItem("notificaciones_simuladas", JSON.stringify(buzon));

    } catch (e) { console.error("Error generando notificación simulada:", e); }
}

async function cargarVistaMisInscripciones() {
    const header = document.getElementById("dinamicHeader");
    const grid = document.getElementById("gridEventos");
    
    header.innerHTML = `<h1>Mis Eventos Inscritos</h1>`;
    grid.innerHTML = "<p>Cargando tus inscripciones...</p>";

    try {
        const resp = await fetch("http://localhost/api/v1/eventos/inscripciones/mis-inscripciones", {
            headers: { "Authorization": `Bearer ${token}` }
        });

        if(!resp.ok) throw new Error("Error obteniendo tus inscripciones");
        const inscripciones = await resp.json();

        grid.innerHTML = "";
        
        if(!inscripciones || inscripciones.length === 0) {
            grid.innerHTML = "<p style='color: gray; font-size: 16px;'>Aún no te has inscrito a ningún evento.</p>";
            return;
        }

        inscripciones.forEach(item => {
            const titulo = item.evento_titulo || "Evento sin título";
            const idEvento = item.evento_id || "Desconocido";
            const idInscripcion = item._id || item.id; 
            
            let fechaInscripcion = "Fecha no registrada";
            if(item.fecha_inscripcion) {
                const fechaObj = new Date(item.fecha_inscripcion);
                fechaInscripcion = fechaObj.toLocaleDateString() + " " + fechaObj.toLocaleTimeString();
            }

            const tarjeta = document.createElement("div");
            tarjeta.className = "event-card"; 
            
            tarjeta.innerHTML = `
                <div class="event-icon">🎟️</div>
                <h3 class="event-title">${titulo}</h3>
                <p class="event-meta">🆔 <strong>ID Evento:</strong> ${idEvento}</p>
                <p class="event-meta">📅 <strong>Inscrito el:</strong> ${fechaInscripcion}</p>
                
                <div style="margin-top: 15px; display: flex; justify-content: space-between; align-items: center;">
                    <span class="status-badge" style="background-color: #dff6dd; color: #107c10; border: 1px solid #107c10; padding: 5px 10px; border-radius: 15px; font-weight: bold; font-size: 12px;">
                        ✔️ ACTIVA
                    </span>
                    <button style="background-color: #d13438; color: white; border: none; padding: 6px 12px; border-radius: 5px; cursor: pointer; font-weight: bold;" 
                            onclick="cancelarInscripcion('${idInscripcion}', '${titulo}')">
                        ❌ Cancelar
                    </button>
                </div>
            `;
            grid.appendChild(tarjeta);
        });

    } catch(e) {
        console.error("Error al cargar mis inscripciones:", e);
        grid.innerHTML = "<p style='color:red;'>Error al cargar tus inscripciones. Verifica que el microservicio esté encendido y la ruta exista.</p>";
    }
}

async function cancelarInscripcion(inscripcionId, eventoTitulo) {
    confirmarAccion(`¿Estás seguro de que deseas cancelar tu participación en:\n"${eventoTitulo}"?`, async () => {
        try {
            const resp = await fetch(`http://localhost/api/v1/eventos/inscripciones/${inscripcionId}`, {
                method: "DELETE",
                headers: { 
                    "Authorization": `Bearer ${token}` 
                }
            });

            if (resp.ok) {
                mostrarToast("Participación cancelada exitosamente.", "success");
                cargarVistaMisInscripciones();
            } else {
                const err = await resp.json();
                mostrarToast("No se pudo cancelar la inscripción: " + (err.detail || "Error del servidor"), "error");
            }
        } catch(e) {
            console.error("Error al cancelar:", e);
            mostrarToast("Error de red intentando cancelar la inscripción.", "error");
        }
    });
}