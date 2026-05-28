// js/notificaciones.js

async function cargarVistaNotificaciones() {
    const header = document.getElementById("dinamicHeader");
    header.innerHTML = `
        <div>
            <h2>📬 Buzón de Correos del Sistema</h2>
            <p style="color: #605e5c; font-size: 14px; margin-top: 5px;">
                Panel de monitoreo para ver los correos disparados por los microservicios.
            </p>
        </div>
        <button class="btn-primary" style="background-color: #0078d4;" onclick="cargarBuzonNotificaciones()">
            🔄 Actualizar Buzón
        </button>
    `;

    const grid = document.getElementById("gridEventos");
    grid.style.display = "flex";
    grid.style.flexDirection = "column";
    grid.style.gap = "15px";
    
    await cargarBuzonNotificaciones();
}

async function cargarBuzonNotificaciones() {
    const grid = document.getElementById("gridEventos");
    grid.innerHTML = '<p style="color: #605e5c;">Consultando buzón...</p>';

    try {
        const rol = localStorage.getItem("usuario_rol");
        const payloadDecodificado = JSON.parse(atob(token.split('.')[1]));
        const miId = parseInt(payloadDecodificado.sub || 0);

        // 1. Obtener correos REALES del backend
        let correosBackend = [];
        try {
            correosBackend = await peticionSegura("/notificaciones/buzon", { method: "GET" });
        } catch(err) {
            console.warn("El microservicio de notificaciones está offline o falló.");
        }

        // Filtro inteligente para los del Backend
        const correosFiltradosBackend = correosBackend.filter(correo => {
            const asunto = (correo.asunto || "").toLowerCase();
            if (rol === "secretariaAcademica") {
                return asunto.includes("creado") || asunto.includes("registrado") || asunto.includes("nuevo") || asunto.includes("pendiente");
            }
            if (rol === "docente") {
                return asunto.includes("aprobado") || asunto.includes("rechazado");
            }
            if (rol === "estudiante") {
                return asunto.includes("aprobado");
            }
            return false;
        });

        // 2. Obtener correos SIMULADOS del LocalStorage (las inscripciones)
        const correosSimulados = JSON.parse(localStorage.getItem("notificaciones_simuladas")) || [];
        
        // Filtramos para que SOLO el dueño del evento vea su notificación simulada
        const misCorreosSimulados = correosSimulados.filter(c => c.destinatarioId === miId);

        // 3. Unir ambas listas
        const todosLosCorreos = [...correosFiltradosBackend, ...misCorreosSimulados];

        // Ordenarlos por fecha (los más nuevos primero)
        todosLosCorreos.sort((a, b) => new Date(b.fecha) - new Date(a.fecha));

        if (todosLosCorreos.length === 0) {
            grid.innerHTML = `
                <div style="background: white; padding: 40px; border-radius: 8px; text-align: center; border: 1px solid #e1dfdd;">
                    <h3 style="color: #323130; margin-bottom: 10px;">📭 El buzón está vacío</h3>
                    <p style="color: #605e5c;">No tienes notificaciones nuevas o relevantes para tu perfil.</p>
                </div>
            `;
            return;
        }

        grid.innerHTML = ""; 

        // ==========================================
        // 4. RENDERIZADO VISUAL
        // ==========================================
        todosLosCorreos.forEach(correo => {
            const fechaFormateada = new Date(correo.fecha).toLocaleString();

            let asuntoMostrar = correo.asunto;
            let cuerpoMostrar = correo.cuerpo;

            // MAGIA UX Estudiante
            if (rol === "estudiante" && asuntoMostrar.toLowerCase().includes("aprobado")) {
                asuntoMostrar = "🎉 ¡Estás invitado a un nuevo evento!";
                cuerpoMostrar = "Se ha abierto un nuevo espacio. ¡Corre a la pestaña de Eventos y asegura tu cupo antes de que se agoten!";
            }

            // Identificar si es simulado (para permitir borrarlo)
            const esSimulado = correo.idUnico ? true : false;
            let botonEliminar = "";
            
            if (esSimulado) {
                botonEliminar = `
                    <div style="text-align: right; margin-top: 10px;">
                        <button onclick="eliminarCorreoSimulado('${correo.idUnico}')" style="background: transparent; border: none; color: #d13438; cursor: pointer; font-weight: bold; font-size: 13px;">
                            <i class="fas fa-trash"></i> Eliminar
                        </button>
                    </div>
                `;
            }

            const correoHtml = `
                <div style="background: white; border: 1px solid #e1dfdd; border-radius: 8px; padding: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.02);">
                    <div style="display: flex; justify-content: space-between; border-bottom: 1px solid #f3f2f1; padding-bottom: 12px; margin-bottom: 15px; font-size: 13px;">
                        <span>
                            <strong style="color: #323130;">De:</strong> ${correo.remitente || 'Sistema'} &nbsp; ➡️ &nbsp; 
                            <strong style="color: #323130;">Para:</strong> 
                            <span style="background: #e1dfdd; padding: 4px 10px; border-radius: 12px; color: #323130;">${correo.destinatario || 'Tí'}</span>
                        </span>
                        <span style="color: #605e5c;">${fechaFormateada}</span>
                    </div>
                    <div>
                        <h4 style="margin: 0 0 15px 0; color: #0078d4;">Asunto: ${asuntoMostrar}</h4>
                        <div style="background: #faf9f8; padding: 15px; border-radius: 6px; border: 1px solid #edebe9; font-size: 14px; color: #323130; overflow-x: auto; min-height: 50px;">
                            ${cuerpoMostrar}
                        </div>
                    </div>
                    ${botonEliminar}
                </div>
            `;
            grid.innerHTML += correoHtml;
        });

    } catch (error) {
        console.error(error);
        grid.innerHTML = `
            <div style="background: #fde7e9; color: #a80000; padding: 15px; border-radius: 8px; border: 1px solid #f9d9dc;">
                <strong>❌ Error Crítico:</strong> Fallo al cargar las notificaciones.
            </div>
        `;
    }
}

// Para borrar un correo simulado de la bandeja
window.eliminarCorreoSimulado = function(idUnico) {
    confirmarAccion("¿Eliminar esta notificación del buzón?", () => {
        let buzon = JSON.parse(localStorage.getItem("notificaciones_simuladas")) || [];
        buzon = buzon.filter(correo => correo.idUnico !== idUnico);
        localStorage.setItem("notificaciones_simuladas", JSON.stringify(buzon));
        
        mostrarToast("Notificación eliminada", "success");
        cargarBuzonNotificaciones(); 
    });
};