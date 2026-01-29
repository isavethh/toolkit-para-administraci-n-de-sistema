"""
Utilidades de Red - Herramientas para diagnóstico y análisis de red
"""
import socket
import subprocess
import platform
import re
from datetime import datetime
from typing import Optional, List, Dict
from concurrent.futures import ThreadPoolExecutor, as_completed


class NetworkUtils:
    """Utilidades para diagnóstico de red."""
    
    def __init__(self):
        self.is_windows = platform.system().lower() == "windows"
    
    def ping(self, host: str, count: int = 4, timeout: int = 2) -> Dict:
        """
        Ejecuta ping a un host.
        
        Args:
            host: Dirección IP o nombre del host
            count: Número de paquetes a enviar
            timeout: Tiempo de espera en segundos
        
        Returns:
            Diccionario con resultados del ping
        """
        if self.is_windows:
            cmd = ["ping", "-n", str(count), "-w", str(timeout * 1000), host]
        else:
            cmd = ["ping", "-c", str(count), "-W", str(timeout), host]
        
        try:
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True, 
                timeout=timeout * count + 5
            )
            
            output = result.stdout
            success = result.returncode == 0
            
            # Parsear estadísticas
            stats = self._parse_ping_stats(output)
            
            return {
                "host": host,
                "success": success,
                "packets_sent": count,
                "packets_received": stats.get("received", 0),
                "packet_loss": stats.get("loss", 100),
                "avg_time_ms": stats.get("avg", 0),
                "min_time_ms": stats.get("min", 0),
                "max_time_ms": stats.get("max", 0),
                "raw_output": output
            }
        except subprocess.TimeoutExpired:
            return {"host": host, "success": False, "error": "Timeout"}
        except Exception as e:
            return {"host": host, "success": False, "error": str(e)}
    
    def _parse_ping_stats(self, output: str) -> Dict:
        """Parsea las estadísticas del comando ping."""
        stats = {}
        
        # Buscar paquetes recibidos
        if self.is_windows:
            match = re.search(r"Recibidos\s*=\s*(\d+)|Received\s*=\s*(\d+)", output)
            if match:
                stats["received"] = int(match.group(1) or match.group(2))
            
            match = re.search(r"Perdidos\s*=\s*(\d+)|Lost\s*=\s*(\d+)", output)
            if match:
                lost = int(match.group(1) or match.group(2))
                sent = stats.get("received", 0) + lost
                stats["loss"] = (lost / sent * 100) if sent > 0 else 100
            
            match = re.search(r"Media\s*=\s*(\d+)ms|Average\s*=\s*(\d+)ms", output)
            if match:
                stats["avg"] = int(match.group(1) or match.group(2))
        else:
            match = re.search(r"(\d+)\s+received", output)
            if match:
                stats["received"] = int(match.group(1))
            
            match = re.search(r"(\d+(?:\.\d+)?)\s*%\s*packet loss", output)
            if match:
                stats["loss"] = float(match.group(1))
            
            match = re.search(r"min/avg/max.*?=\s*([\d.]+)/([\d.]+)/([\d.]+)", output)
            if match:
                stats["min"] = float(match.group(1))
                stats["avg"] = float(match.group(2))
                stats["max"] = float(match.group(3))
        
        return stats
    
    def traceroute(self, host: str, max_hops: int = 30) -> Dict:
        """
        Ejecuta traceroute a un host.
        
        Args:
            host: Dirección IP o nombre del host
            max_hops: Número máximo de saltos
        
        Returns:
            Diccionario con resultados del traceroute
        """
        if self.is_windows:
            cmd = ["tracert", "-d", "-h", str(max_hops), host]
        else:
            cmd = ["traceroute", "-n", "-m", str(max_hops), host]
        
        try:
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True, 
                timeout=60
            )
            
            hops = self._parse_traceroute(result.stdout)
            
            return {
                "host": host,
                "success": result.returncode == 0,
                "hops": hops,
                "total_hops": len(hops),
                "raw_output": result.stdout
            }
        except subprocess.TimeoutExpired:
            return {"host": host, "success": False, "error": "Timeout"}
        except Exception as e:
            return {"host": host, "success": False, "error": str(e)}
    
    def _parse_traceroute(self, output: str) -> List[Dict]:
        """Parsea la salida del traceroute."""
        hops = []
        lines = output.strip().split('\n')
        
        for line in lines:
            # Buscar líneas con número de salto
            match = re.search(r"^\s*(\d+)\s+", line)
            if match:
                hop_num = int(match.group(1))
                
                # Buscar IPs
                ips = re.findall(r"\b(\d+\.\d+\.\d+\.\d+)\b", line)
                
                # Buscar tiempos
                times = re.findall(r"(\d+(?:\.\d+)?)\s*ms", line)
                
                hop = {
                    "hop": hop_num,
                    "ip": ips[0] if ips else "*",
                    "times_ms": [float(t) for t in times] if times else []
                }
                hops.append(hop)
        
        return hops
    
    def dns_lookup(self, hostname: str) -> Dict:
        """
        Realiza búsqueda DNS de un hostname.
        
        Args:
            hostname: Nombre de dominio a resolver
        
        Returns:
            Diccionario con resultados DNS
        """
        result = {
            "hostname": hostname,
            "success": False,
            "ip_addresses": [],
            "aliases": []
        }
        
        try:
            # Obtener información del host
            info = socket.gethostbyname_ex(hostname)
            result["success"] = True
            result["canonical_name"] = info[0]
            result["aliases"] = info[1]
            result["ip_addresses"] = info[2]
        except socket.gaierror as e:
            result["error"] = f"No se pudo resolver: {e}"
        except Exception as e:
            result["error"] = str(e)
        
        return result
    
    def reverse_dns(self, ip_address: str) -> Dict:
        """
        Realiza búsqueda DNS inversa de una IP.
        
        Args:
            ip_address: Dirección IP a resolver
        
        Returns:
            Diccionario con resultados
        """
        result = {
            "ip_address": ip_address,
            "success": False,
            "hostname": None
        }
        
        try:
            hostname = socket.gethostbyaddr(ip_address)
            result["success"] = True
            result["hostname"] = hostname[0]
            result["aliases"] = hostname[1]
        except socket.herror as e:
            result["error"] = f"No se encontró hostname: {e}"
        except Exception as e:
            result["error"] = str(e)
        
        return result
    
    def check_host_availability(self, hosts: List[str]) -> List[Dict]:
        """
        Verifica disponibilidad de múltiples hosts en paralelo.
        
        Args:
            hosts: Lista de hosts a verificar
        
        Returns:
            Lista de resultados
        """
        results = []
        
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = {executor.submit(self.ping, host, 2): host for host in hosts}
            
            for future in as_completed(futures):
                results.append(future.result())
        
        return results
    
    def get_local_ip(self) -> str:
        """Obtiene la IP local del equipo."""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return "127.0.0.1"
    
    def get_public_ip(self) -> Optional[str]:
        """Obtiene la IP pública del equipo (requiere conexión a internet)."""
        import urllib.request
        
        services = [
            "https://api.ipify.org",
            "https://icanhazip.com",
            "https://ipinfo.io/ip"
        ]
        
        for service in services:
            try:
                with urllib.request.urlopen(service, timeout=5) as response:
                    return response.read().decode('utf-8').strip()
            except Exception:
                continue
        
        return None
    
    def port_check(self, host: str, port: int, timeout: float = 2.0) -> Dict:
        """
        Verifica si un puerto está abierto.
        
        Args:
            host: Host a verificar
            port: Puerto a verificar
            timeout: Tiempo de espera
        
        Returns:
            Diccionario con el resultado
        """
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            result = sock.connect_ex((host, port))
            sock.close()
            
            is_open = result == 0
            
            # Intentar obtener el nombre del servicio
            try:
                service = socket.getservbyport(port)
            except OSError:
                service = "desconocido"
            
            return {
                "host": host,
                "port": port,
                "is_open": is_open,
                "service": service if is_open else None
            }
        except socket.error as e:
            return {"host": host, "port": port, "is_open": False, "error": str(e)}


def print_ping_result(result: Dict):
    """Imprime el resultado de un ping."""
    print(f"\n  {'='*50}")
    print(f"  PING a {result['host']}")
    print(f"  {'='*50}")
    
    if result.get("success"):
        print(f"  ✓ Host alcanzable")
        print(f"  Paquetes: {result['packets_received']}/{result['packets_sent']} recibidos")
        print(f"  Pérdida: {result['packet_loss']:.1f}%")
        if result.get('avg_time_ms'):
            print(f"  Tiempo promedio: {result['avg_time_ms']} ms")
    else:
        print(f"  ✗ Host no alcanzable")
        if result.get("error"):
            print(f"  Error: {result['error']}")


def print_traceroute_result(result: Dict):
    """Imprime el resultado de un traceroute."""
    print(f"\n  {'='*50}")
    print(f"  TRACEROUTE a {result['host']}")
    print(f"  {'='*50}")
    
    if result.get("success"):
        for hop in result['hops']:
            times = ", ".join(f"{t}ms" for t in hop['times_ms']) if hop['times_ms'] else "*"
            print(f"  {hop['hop']:3d}  {hop['ip']:15}  {times}")
    else:
        print(f"  Error: {result.get('error', 'Desconocido')}")


def run_network_diagnostic():
    """Ejecuta diagnóstico interactivo de red."""
    utils = NetworkUtils()
    
    while True:
        print("\n" + "="*60)
        print("  UTILIDADES DE RED")
        print("="*60)
        print("\n  Opciones:")
        print("  1. Ping a host")
        print("  2. Traceroute")
        print("  3. Búsqueda DNS")
        print("  4. DNS Inverso")
        print("  5. Verificar múltiples hosts")
        print("  6. Ver IP local/pública")
        print("  7. Verificar puerto específico")
        print("  8. Volver")
        
        opcion = input("\n  Seleccione (1-8): ").strip()
        
        if opcion == "1":
            host = input("  Host a hacer ping: ").strip()
            count = input("  Número de paquetes (4): ").strip()
            count = int(count) if count.isdigit() else 4
            
            print("\n  Ejecutando ping...")
            result = utils.ping(host, count)
            print_ping_result(result)
        
        elif opcion == "2":
            host = input("  Host destino: ").strip()
            print("\n  Ejecutando traceroute (puede tardar)...")
            result = utils.traceroute(host)
            print_traceroute_result(result)
        
        elif opcion == "3":
            hostname = input("  Dominio a resolver: ").strip()
            result = utils.dns_lookup(hostname)
            
            print(f"\n  DNS Lookup: {hostname}")
            if result['success']:
                print(f"  IPs encontradas: {', '.join(result['ip_addresses'])}")
                if result['aliases']:
                    print(f"  Aliases: {', '.join(result['aliases'])}")
            else:
                print(f"  Error: {result.get('error')}")
        
        elif opcion == "4":
            ip = input("  IP a resolver: ").strip()
            result = utils.reverse_dns(ip)
            
            print(f"\n  DNS Inverso: {ip}")
            if result['success']:
                print(f"  Hostname: {result['hostname']}")
            else:
                print(f"  Error: {result.get('error')}")
        
        elif opcion == "5":
            hosts_input = input("  Hosts (separados por coma): ").strip()
            hosts = [h.strip() for h in hosts_input.split(",")]
            
            print("\n  Verificando hosts...")
            results = utils.check_host_availability(hosts)
            
            print(f"\n  {'HOST':<30} {'ESTADO':<12} {'TIEMPO'}")
            print("  " + "-"*55)
            for r in results:
                status = "✓ OK" if r.get('success') else "✗ FAIL"
                time_ms = f"{r.get('avg_time_ms', 0)}ms" if r.get('success') else "-"
                print(f"  {r['host']:<30} {status:<12} {time_ms}")
        
        elif opcion == "6":
            local_ip = utils.get_local_ip()
            print(f"\n  IP Local: {local_ip}")
            
            print("  Obteniendo IP pública...")
            public_ip = utils.get_public_ip()
            if public_ip:
                print(f"  IP Pública: {public_ip}")
            else:
                print("  No se pudo obtener la IP pública")
        
        elif opcion == "7":
            host = input("  Host: ").strip()
            port = input("  Puerto: ").strip()
            
            if port.isdigit():
                result = utils.port_check(host, int(port))
                status = "ABIERTO" if result['is_open'] else "CERRADO"
                print(f"\n  Puerto {port} en {host}: {status}")
                if result.get('service'):
                    print(f"  Servicio: {result['service']}")
            else:
                print("  Puerto inválido")
        
        elif opcion == "8":
            break


if __name__ == "__main__":
    run_network_diagnostic()
