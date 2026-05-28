# Levantar la infraestructura de contenedores Docker-in-Docker
Write-Host "Levantando contenedores manager, worker1 y worker2..."
docker-compose -f docker-compose-dind.yml up -d

# Esperar un poco para asegurar que el servicio de Docker dentro de dind inicie correctamente
Write-Host "Esperando a que los daemons de Docker internos inicien (10 segundos)..."
Start-Sleep -Seconds 10

# Inicializar Swarm en el manager
Write-Host "Inicializando Docker Swarm en el manager..."
docker exec manager docker swarm init

# Obtener el token de join para los workers
$TOKEN = docker exec manager docker swarm join-token -q worker

# Unir worker1 al Swarm
Write-Host "Uniendo worker1 al Swarm..."
docker exec worker1 docker swarm join --token $TOKEN manager:2377

# Unir worker2 al Swarm
Write-Host "Uniendo worker2 al Swarm..."
docker exec worker2 docker swarm join --token $TOKEN manager:2377

# Desplegar el stack
Write-Host "Desplegando la aplicación en el Swarm (universidad_stack)..."
docker exec manager docker stack deploy -c /docker-compose.yml universidad_stack

Write-Host "¡Despliegue completado exitosamente!"
Write-Host "Puedes revisar el estado de los servicios ejecutando: docker exec manager docker service ls"
