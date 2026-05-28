Write-Host "============================================="
Write-Host " Iniciando Cluster Docker Swarm (DinD)"
Write-Host "============================================="

Write-Host "1. Limpiando y levantando nodos virtuales (Manager y Workers)..."
docker-compose -f docker-compose-dind.yml down -v
docker-compose -f docker-compose-dind.yml up -d

Write-Host "Esperando 10 segundos a que Docker inicie dentro de los nodos..."
Start-Sleep -Seconds 10

Write-Host "2. Inicializando Swarm en el Manager..."
$initResult = docker exec manager docker swarm init 2>&1
if ($initResult -match "Swarm initialized" -or $initResult -match "join-token") {
    Write-Host "Swarm inicializado. Obteniendo token de worker..."
    $TOKEN = docker exec manager docker swarm join-token -q worker
    
    Write-Host "Uniendo Worker 1 al Swarm..."
    docker exec worker1 docker swarm join --token $TOKEN manager:2377
    
    Write-Host "Uniendo Worker 2 al Swarm..."
    docker exec worker2 docker swarm join --token $TOKEN manager:2377
} else {
    Write-Host "El Swarm ya estaba inicializado."
}

Write-Host "3. Configurando DNS y copiando el codigo fuente al Manager..."
docker exec manager sh -c "echo 'nameserver 8.8.8.8' > /etc/resolv.conf"
# Copiamos todo el backend al directorio /app dentro del manager
docker exec manager mkdir -p /app
docker cp . manager:/app/

Write-Host "4. Construyendo imagenes de los microservicios y PySpark..."
# Hacemos build dentro del manager usando el cA3digo copiado en /app
docker exec manager sh -c "cd /app && docker compose build"

Write-Host "5. Desplegando el stack completo en Swarm..."
docker exec manager sh -c "cd /app && docker stack deploy -c docker-compose.yml universidad_stack"

Write-Host "============================================="
Write-Host " Despliegue completado con Exito!"
Write-Host " Los contenedores se estan levantando en background."
Write-Host " Puedes probar la aplicacion en: http://localhost"
Write-Host "============================================="
