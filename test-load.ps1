Write-Host "Enviando 10 peticiones al servicio whoami (localhost:8000) desde dentro del clúster Swarm..."
Write-Host "--------------------------------------------------------------------------------------------------------"

for ($i=1; $i -le 10; $i++) {
    try {
        # Ejecutamos wget directamente dentro del manager para evitar el problema de puertos no expuestos en Windows
        $response = docker exec manager wget -qO- http://localhost:8000/
        $hostname = ($response -split "`n" | Where-Object { $_ -match "^Hostname:" }).Trim()
        Write-Host "Petición $i -> Atendida por el contenedor: $hostname"
    } catch {
        Write-Host "Petición $i -> Error: $_"
    }
    Start-Sleep -Milliseconds 200
}
Write-Host "--------------------------------------------------------------------------------------------------------"
Write-Host "Si ves distintos Hostnames, ¡Swarm está balanceando exitosamente las peticiones entre los distintos workers!"
