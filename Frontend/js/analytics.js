// js/analytics.js

async function cargarVistaAnalytics() {
    const header = document.getElementById("dinamicHeader");
    header.innerHTML = `<h1>📊 Dashboard Analítico (Powered by PySpark)</h1>`;

    const grid = document.getElementById("gridEventos");
    grid.innerHTML = `
        <div style="text-align: center; padding: 40px; color: #666;">
            <i class="fas fa-spinner fa-spin fa-3x"></i>
            <p style="margin-top: 15px; font-size: 16px;">PySpark está procesando los datos en tiempo real...</p>
        </div>
    `;

    try {
        const resp = await fetch("http://localhost/api/v1/analytics/estadisticas");
        const data = await resp.json();

        if (data.status !== "success" || !data.estadisticas) {
            grid.innerHTML = `<p style="color: red;">No hay suficientes datos o hubo un error en PySpark: ${data.message}</p>`;
            return;
        }

        const est = data.estadisticas;
        const agp = est.agrupaciones;

        grid.innerHTML = `
            <div style="display: flex; gap: 20px; margin-bottom: 30px; flex-wrap: wrap;">
                <div class="stat-card" style="flex: 1; min-width: 200px; background: #fff; padding: 20px; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); text-align: center;">
                    <h3 style="color: #5c2d91; margin: 0; font-size: 32px;">${est.total_registros_procesados}</h3>
                    <p style="color: #666; margin: 5px 0 0 0;">Eventos Procesados</p>
                </div>
                <div class="stat-card" style="flex: 1; min-width: 200px; background: #fff; padding: 20px; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); text-align: center;">
                    <h3 style="color: #107c10; margin: 0; font-size: 32px;">${agp.ocupacion ? agp.ocupacion.ocupacion_promedio_porcentual : 0}%</h3>
                    <p style="color: #666; margin: 5px 0 0 0;">Ocupación Promedio Global</p>
                </div>
                <div class="stat-card" style="flex: 1; min-width: 200px; background: #fff; padding: 20px; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); text-align: center;">
                    <h3 style="color: #0078d4; margin: 0; font-size: 32px;">${agp.ocupacion ? agp.ocupacion.total_inscritos : 0}</h3>
                    <p style="color: #666; margin: 5px 0 0 0;">Inscripciones Totales</p>
                </div>
            </div>

            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px;">
                <div style="background: #fff; padding: 20px; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
                    <h4 style="margin-top: 0;">Eventos por Estado</h4>
                    <canvas id="chartEstado"></canvas>
                </div>
                <div style="background: #fff; padding: 20px; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
                    <h4 style="margin-top: 0;">Eventos por Tipo</h4>
                    <canvas id="chartTipo"></canvas>
                </div>
                <div style="background: #fff; padding: 20px; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); grid-column: 1 / -1;">
                    <h4 style="margin-top: 0;">Top Docentes Más Activos (ID)</h4>
                    <canvas id="chartDocentes" height="80"></canvas>
                </div>
            </div>
        `;

        // Renderizar Gráficos con Chart.js
        if(agp.por_estado) {
            new Chart(document.getElementById('chartEstado'), {
                type: 'doughnut',
                data: {
                    labels: agp.por_estado.map(e => e.estado.toUpperCase()),
                    datasets: [{
                        data: agp.por_estado.map(e => e.cantidad),
                        backgroundColor: ['#d13438', '#107c10', '#0078d4', '#5c2d91']
                    }]
                }
            });
        }

        if(agp.por_tipo) {
            new Chart(document.getElementById('chartTipo'), {
                type: 'pie',
                data: {
                    labels: agp.por_tipo.map(e => e.tipo.toUpperCase()),
                    datasets: [{
                        data: agp.por_tipo.map(e => e.cantidad),
                        backgroundColor: ['#ffb900', '#e3008c']
                    }]
                }
            });
        }

        if(agp.top_docentes) {
            new Chart(document.getElementById('chartDocentes'), {
                type: 'bar',
                data: {
                    labels: agp.top_docentes.map(e => "Docente ID: " + e.creadoPor),
                    datasets: [{
                        label: 'Cantidad de Eventos',
                        data: agp.top_docentes.map(e => e.cantidad_eventos),
                        backgroundColor: '#0078d4'
                    }]
                },
                options: { scales: { y: { beginAtZero: true } } }
            });
        }

    } catch(e) {
        grid.innerHTML = `<p style="color: red;">Error al cargar datos desde PySpark: ${e.message}</p>`;
    }
}
