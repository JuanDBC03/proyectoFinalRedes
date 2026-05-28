# Creado por:
Juan David Bedoya,
Sebastian Rojas

# Sistema de Gestión Universitaria (Arquitectura de Microservicios)

Bienvenido al repositorio oficial del Sistema de Gestión Universitaria. Este proyecto final de redes demuestra una arquitectura avanzada basada en microservicios, contenedorizada con Docker, orquestada mediante Docker Swarm y potenciada por analítica de grandes datos usando Apache Spark (PySpark).

---

## Criterios de Evaluación del Proyecto

Este sistema ha sido diseñado rigurosamente para cumplir y exceder los estándares de ingeniería de software modernos:

1. **Arquitectura Distribuida:** Operamos sobre un clúster de Docker Swarm (1 Manager, 2 Workers). Las réplicas de los microservicios se distribuyen dinámicamente entre los nodos trabajadores, mientras que un API Gateway (Nginx) balancea la carga de red entrante.
2. **Separación de Servicios:** Arquitectura estricta de microservicios por dominio de negocio (Autenticación, Usuarios, Eventos, Instalaciones, Evaluaciones, Notificaciones, Analítica). Cada servicio es autónomo y desacoplado.
3. **Despliegue Reproducible:** Infraestructura automatizada (IaC). Basta con ejecutar el script `iniciar_proyecto.ps1` para inicializar nodos, crear redes overlay, compilar imágenes, distribuir cachés entre nodos worker y desplegar el stack completo sin intervención manual.
4. **Procesamiento de Datos:** Incorporación de Apache PySpark para ejecutar pipelines ETL (Extract, Transform, Load) en memoria, procesando cientos de registros encolados en MongoDB y generando métricas estadísticas complejas expuestas vía REST.
5. **Buenas Prácticas de Ingeniería:** Uso de FastAPI (Python asíncrono), JWT para seguridad, Beanie ODM para interacción orientada a objetos con MongoDB, políticas de reinicio automático ante fallos, sembrado masivo de datos automático (Data Seeding) y separación Frontend/Backend.

---

## Arquitectura del Sistema

El sistema ha sido desacoplado en componentes independientes para garantizar alta disponibilidad, escalabilidad y tolerancia a fallos.

### Microservicios Desarrollados (Backend)
Todos los servicios exponen una API RESTful documentada usando FastAPI (Python):
1. **auth_service (Puerto 8001):** Emisión y validación de tokens JWT (JSON Web Tokens). Maneja la seguridad centralizada.
2. **usuarios_service (Puerto 8002):** Operaciones CRUD de usuarios. Diferenciación por roles (Estudiante, Docente, Secretaría Académica).
3. **eventos_service (Puerto 8003):** Lógica central. Maneja la creación de eventos, flujo de aprobaciones, asignación de instalaciones y registro masivo de inscripciones.
4. **evaluaciones_service (Puerto 8004):** Flujo de trabajo para asentar dictámenes académicos (Aprobado/Rechazado) por parte de la Secretaría Académica.
5. **instalaciones_service (Puerto 8005):** Gestión del espacio físico de la universidad (Auditorios, Laboratorios, Salones, etc.) y control de capacidad máxima.
6. **notificaciones_service (Puerto 8006):** Envío asíncrono de correos electrónicos a los estudiantes cuando son confirmados o rechazados de un evento. Se integra con MailHog para simulación SMTP.

### Capa de Analítica de Datos (Big Data)
- **analytics_service (Puerto 8007):** Este microservicio integra Apache Spark (PySpark) y Java 11 para conectarse de forma paralela a la base de datos de MongoDB. Extrae los registros de la colección de eventos y ejecuta trabajos de transformación y agregación (ETL Distribuido) en memoria para generar tableros de mando (Dashboards).

### Capa de Persistencia
- **mongo (Puerto 27017):** Base de datos NoSQL centralizada. Todos los microservicios se conectan a ella usando el framework ODM asíncrono Beanie/Motor.

### API Gateway / Frontend
- **nginx (Puerto 80):** Actúa como balanceador de carga y proxy inverso. Intercepta todo el tráfico que entra por localhost y lo enruta al microservicio correspondiente basado en la URI (ej. /api/v1/eventos). También sirve de manera estática la interfaz gráfica (HTML/CSS/JS).

---

## Orquestación: Docker Swarm (Docker-in-Docker)

El proyecto utiliza un clúster de Docker Swarm simulado localmente mediante la técnica DinD (Docker in Docker), logrando ejecutar múltiples nodos virtuales en una sola máquina anfitriona.

- **Manager:** Nodo líder. Expone el puerto 80 al host, mantiene el estado del clúster y distribuye imágenes compiladas localmente a los workers (`docker save`/`docker load`).
- **Worker 1 & 2:** Nodos de trabajo. Ejecutan las réplicas de los microservicios, aliviando la carga del manager.

> **Routing Mesh (Malla de Enrutamiento):** Swarm balancea las peticiones (Round Robin) garantizando que si una instancia de un servicio se interrumpe, otra responderá automáticamente sin que el cliente (Frontend) perciba la caída.

---

## Guía de Instalación y Despliegue (Paso a Paso)

Siga estos pasos para desplegar el proyecto desde cero en un entorno local:

### Requisitos Previos
- Docker Desktop instalado y en ejecución en Windows o macOS.
- PowerShell o Bash.

### Instrucciones

1. **Abra PowerShell** y navegue a la raíz del repositorio (`backend/backend`).
2. **Ejecute el script de inicio automático:**
   ```powershell
   .\iniciar_proyecto.ps1
   ```
3. **Procesos internos del script:**
   - Elimina cualquier clúster anterior.
   - Inicia tres contenedores simulando máquinas físicas (`manager`, `worker1`, `worker2`).
   - El manager inicializa el clúster (`docker swarm init`) y los workers se unen a él.
   - Copia el código fuente al nodo `manager`.
   - Ejecuta `docker compose build` internamente para compilar todas las imágenes (incluyendo el entorno de Java/Python para PySpark).
   - Exporta las imágenes construidas y las carga en los nodos worker para permitir una verdadera distribución de tareas en Swarm, sin depender de repositorios externos como Docker Hub.
   - Finalmente, despliega todos los microservicios usando `docker stack deploy -c docker-compose.yml universidad_stack`.
4. **Verificación:**
   Puede comprobar que los servicios se han distribuido correctamente en los workers ejecutando el siguiente comando:
   ```bash
   docker exec manager docker service ps universidad_stack_usuarios_service
   ```
5. **Acceso al sistema:** Abra su navegador web en `http://localhost` para interactuar con la plataforma.

---

## Panel de Control y Frontend

El Frontend está desarrollado de forma nativa utilizando Vanilla JS, HTML5 y CSS3 para maximizar el rendimiento y evitar dependencias de compilación adicionales.

### Funcionalidades:
- **Autenticación Basada en Roles:** Despliega interfaces específicas para Estudiantes, Docentes y miembros de la Secretaría.
- **Búsqueda Global Inteligente:** Barra de búsqueda en tiempo real que normaliza el texto (ignorando mayúsculas, tildes y acentos) para localizar eventos, usuarios e instalaciones de forma precisa y robusta.
- **Dashboard Analítico (PySpark):** Interfaz dedicada e independiente (`/analytics.html`) que solicita estadísticas procesadas por el servicio de Spark en el backend, renderizando gráficos (como diagramas de sectores y barras) mediante la librería Chart.js.

---

## Referencias y Tecnologías

- [FastAPI](https://fastapi.tiangolo.com/): Framework web de alto rendimiento para APIs en Python.
- [Apache Spark (PySpark)](https://spark.apache.org/docs/latest/api/python/): Motor de analítica unificada para procesamiento masivo de datos.
- [Docker Swarm](https://docs.docker.com/engine/swarm/): Orquestador nativo de clústeres para contenedores Docker.
- [Beanie ODM](https://beanie-odm.dev/): Mapeador de Objetos y Documentos (ODM) asíncrono para MongoDB basado en Pydantic.
- [NGINX](https://nginx.org/): Servidor web y API Gateway.
- [Chart.js](https://www.chartjs.org/): Librería de gráficos en JavaScript orientada a tableros de control analíticos.
