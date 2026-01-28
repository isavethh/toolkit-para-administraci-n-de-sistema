"""
Escáner de puertos - Herramienta para escanear puertos abiertos en un host
"""
import socket
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime


def scan_port(host: str, port: int, timeout: float = 1.0) -> dict:
    """Escanea un puerto específico en un host."""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((host, port))
        sock.close()
        
        if result == 0:
            try:
                service = socket.getservbyport(port)
            except OSError:
                service = "desconocido"
            return {"port": port, "status": "abierto", "service": service}
        return {"port": port, "status": "cerrado", "service": None}
    except socket.error as e:
        return {"port": port, "status": "error", "service": None, "error": str(e)}


def scan_ports(host: str, start_port: int = 1, end_port: int = 1024, 
               timeout: float = 1.0, max_workers: int = 100) -> list:
    """
    Escanea un rango de puertos en un host usando múltiples hilos.
    
    Args:
        host: Dirección IP o nombre del host
        start_port: Puerto inicial del rango
        end_port: Puerto final del rango
        timeout: Tiempo de espera por conexión (segundos)
        max_workers: Número máximo de hilos concurrentes
    
    Returns:
        Lista de diccionarios con información de puertos abiertos
    """
    open_ports = []
    
    print(f"\n{'='*60}")
    print(f"  Escáner de Puertos")
    print(f"{'='*60}")
    print(f"  Host objetivo: {host}")
    print(f"  Rango de puertos: {start_port} - {end_port}")
    print(f"  Inicio: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}\n")
    
    try:
        target_ip = socket.gethostbyname(host)
        print(f"  IP resuelta: {target_ip}\n")
    except socket.gaierror:
        print(f"  [ERROR] No se pudo resolver el host: {host}")
        return []
    
    ports_to_scan = range(start_port, end_port + 1)
    total_ports = len(ports_to_scan)
    scanned = 0
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(scan_port, host, port, timeout): port 
                   for port in ports_to_scan}
        
        for future in as_completed(futures):
            scanned += 1
            result = future.result()
            
            if result["status"] == "abierto":
                open_ports.append(result)
                print(f"  [+] Puerto {result['port']:5d}/tcp ABIERTO - {result['service']}")
            
            # Mostrar progreso cada 100 puertos
            if scanned % 100 == 0:
                print(f"  ... Progreso: {scanned}/{total_ports} puertos escaneados")
    
    print(f"\n{'='*60}")
    print(f"  Escaneo completado")
    print(f"  Puertos abiertos encontrados: {len(open_ports)}")
    print(f"  Fin: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}\n")
    
    return sorted(open_ports, key=lambda x: x["port"])


def quick_scan(host: str) -> list:
    """Escaneo rápido de puertos comunes."""
    common_ports = [
        21, 22, 23, 25, 53, 80, 110, 135, 139, 143, 443, 445, 
        993, 995, 1433, 1521, 3306, 3389, 5432, 5900, 8080, 8443
    ]
    
    print(f"\n{'='*60}")
    print(f"  Escaneo Rápido - Puertos Comunes")
    print(f"{'='*60}")
    print(f"  Host: {host}")
    print(f"  Puertos a escanear: {len(common_ports)}")
    print(f"{'='*60}\n")
    
    open_ports = []
    for port in common_ports:
        result = scan_port(host, port, timeout=0.5)
        if result["status"] == "abierto":
            open_ports.append(result)
            print(f"  [+] Puerto {result['port']:5d}/tcp ABIERTO - {result['service']}")
    
    print(f"\n  Total puertos abiertos: {len(open_ports)}\n")
    return open_ports


if __name__ == "__main__":
    # Ejemplo de uso
    target = input("Ingrese el host a escanear (ej: localhost, 192.168.1.1): ").strip()
    
    print("\nOpciones:")
    print("1. Escaneo rápido (puertos comunes)")
    print("2. Escaneo completo (1-1024)")
    print("3. Escaneo personalizado")
    
    opcion = input("\nSeleccione una opción (1-3): ").strip()
    
    if opcion == "1":
        results = quick_scan(target)
    elif opcion == "2":
        results = scan_ports(target, 1, 1024)
    elif opcion == "3":
        start = int(input("Puerto inicial: "))
        end = int(input("Puerto final: "))
        results = scan_ports(target, start, end)
    else:
        print("Opción no válida")
        results = []
    
    if results:
        print("\nResumen de puertos abiertos:")
        for port_info in results:
            print(f"  - {port_info['port']}/tcp ({port_info['service']})")
