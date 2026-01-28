"""
Monitor del Sistema - Herramienta para monitorear recursos del sistema
"""
import os
import platform
import time
from datetime import datetime
from typing import Optional

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    print("[AVISO] psutil no está instalado. Ejecute: pip install psutil")


class SystemMonitor:
    """Monitor de recursos del sistema."""
    
    def __init__(self):
        self.alerts = []
        self.thresholds = {
            "cpu_percent": 80.0,
            "memory_percent": 85.0,
            "disk_percent": 90.0
        }
        self.history = {
            "cpu": [],
            "memory": [],
            "disk": []
        }
    
    def get_system_info(self) -> dict:
        """Obtiene información general del sistema."""
        info = {
            "hostname": platform.node(),
            "os": platform.system(),
            "os_version": platform.version(),
            "architecture": platform.machine(),
            "processor": platform.processor(),
            "python_version": platform.python_version(),
            "timestamp": datetime.now().isoformat()
        }
        
        if PSUTIL_AVAILABLE:
            info["boot_time"] = datetime.fromtimestamp(psutil.boot_time()).isoformat()
            info["uptime_hours"] = round((time.time() - psutil.boot_time()) / 3600, 2)
        
        return info
    
    def get_cpu_stats(self) -> dict:
        """Obtiene estadísticas de CPU."""
        if not PSUTIL_AVAILABLE:
            return {"error": "psutil no disponible"}
        
        cpu_percent = psutil.cpu_percent(interval=1)
        cpu_freq = psutil.cpu_freq()
        cpu_count = psutil.cpu_count()
        cpu_count_logical = psutil.cpu_count(logical=True)
        
        stats = {
            "percent_usage": cpu_percent,
            "cores_physical": cpu_count,
            "cores_logical": cpu_count_logical,
            "frequency_mhz": {
                "current": round(cpu_freq.current, 2) if cpu_freq else 0,
                "min": round(cpu_freq.min, 2) if cpu_freq else 0,
                "max": round(cpu_freq.max, 2) if cpu_freq else 0
            },
            "per_core_percent": psutil.cpu_percent(interval=0.1, percpu=True)
        }
        
        # Registrar en historial
        self.history["cpu"].append({
            "timestamp": datetime.now().isoformat(),
            "value": cpu_percent
        })
        
        # Verificar alertas
        if cpu_percent > self.thresholds["cpu_percent"]:
            self._add_alert("CPU", f"Uso de CPU alto: {cpu_percent}%")
        
        return stats
    
    def get_memory_stats(self) -> dict:
        """Obtiene estadísticas de memoria."""
        if not PSUTIL_AVAILABLE:
            return {"error": "psutil no disponible"}
        
        mem = psutil.virtual_memory()
        swap = psutil.swap_memory()
        
        stats = {
            "ram": {
                "total_gb": round(mem.total / (1024**3), 2),
                "available_gb": round(mem.available / (1024**3), 2),
                "used_gb": round(mem.used / (1024**3), 2),
                "percent_used": mem.percent
            },
            "swap": {
                "total_gb": round(swap.total / (1024**3), 2),
                "used_gb": round(swap.used / (1024**3), 2),
                "percent_used": swap.percent
            }
        }
        
        # Registrar en historial
        self.history["memory"].append({
            "timestamp": datetime.now().isoformat(),
            "value": mem.percent
        })
        
        # Verificar alertas
        if mem.percent > self.thresholds["memory_percent"]:
            self._add_alert("MEMORIA", f"Uso de memoria alto: {mem.percent}%")
        
        return stats
    
    def get_disk_stats(self) -> dict:
        """Obtiene estadísticas de disco."""
        if not PSUTIL_AVAILABLE:
            return {"error": "psutil no disponible"}
        
        partitions = []
        for partition in psutil.disk_partitions():
            try:
                usage = psutil.disk_usage(partition.mountpoint)
                partitions.append({
                    "device": partition.device,
                    "mountpoint": partition.mountpoint,
                    "fstype": partition.fstype,
                    "total_gb": round(usage.total / (1024**3), 2),
                    "used_gb": round(usage.used / (1024**3), 2),
                    "free_gb": round(usage.free / (1024**3), 2),
                    "percent_used": usage.percent
                })
                
                # Verificar alertas por partición
                if usage.percent > self.thresholds["disk_percent"]:
                    self._add_alert("DISCO", f"Disco {partition.mountpoint} al {usage.percent}%")
                    
            except PermissionError:
                continue
        
        # IO Stats
        io_counters = psutil.disk_io_counters()
        io_stats = {
            "read_gb": round(io_counters.read_bytes / (1024**3), 2),
            "write_gb": round(io_counters.write_bytes / (1024**3), 2),
            "read_count": io_counters.read_count,
            "write_count": io_counters.write_count
        } if io_counters else {}
        
        return {
            "partitions": partitions,
            "io_stats": io_stats
        }
    
    def get_network_stats(self) -> dict:
        """Obtiene estadísticas de red."""
        if not PSUTIL_AVAILABLE:
            return {"error": "psutil no disponible"}
        
        net_io = psutil.net_io_counters()
        connections = psutil.net_connections(kind='inet')
        
        # Contar conexiones por estado
        conn_states = {}
        for conn in connections:
            state = conn.status
            conn_states[state] = conn_states.get(state, 0) + 1
        
        # Interfaces de red
        interfaces = []
        net_if = psutil.net_if_addrs()
        for iface_name, addresses in net_if.items():
            for addr in addresses:
                if addr.family.name == 'AF_INET':
                    interfaces.append({
                        "name": iface_name,
                        "ip": addr.address,
                        "netmask": addr.netmask
                    })
        
        return {
            "io": {
                "bytes_sent_gb": round(net_io.bytes_sent / (1024**3), 2),
                "bytes_recv_gb": round(net_io.bytes_recv / (1024**3), 2),
                "packets_sent": net_io.packets_sent,
                "packets_recv": net_io.packets_recv,
                "errors_in": net_io.errin,
                "errors_out": net_io.errout
            },
            "connections": conn_states,
            "total_connections": len(connections),
            "interfaces": interfaces
        }
    
    def get_process_list(self, top_n: int = 10, sort_by: str = "memory") -> list:
        """Obtiene la lista de procesos más consumidores."""
        if not PSUTIL_AVAILABLE:
            return []
        
        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'username', 'cpu_percent', 
                                          'memory_percent', 'status', 'create_time']):
            try:
                info = proc.info
                processes.append({
                    "pid": info['pid'],
                    "name": info['name'],
                    "user": info['username'],
                    "cpu_percent": info['cpu_percent'] or 0,
                    "memory_percent": round(info['memory_percent'] or 0, 2),
                    "status": info['status']
                })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        # Ordenar por criterio seleccionado
        if sort_by == "cpu":
            processes.sort(key=lambda x: x['cpu_percent'], reverse=True)
        else:
            processes.sort(key=lambda x: x['memory_percent'], reverse=True)
        
        return processes[:top_n]
    
    def _add_alert(self, category: str, message: str):
        """Añade una alerta al registro."""
        alert = {
            "timestamp": datetime.now().isoformat(),
            "category": category,
            "message": message
        }
        self.alerts.append(alert)
    
    def get_alerts(self) -> list:
        """Obtiene las alertas activas."""
        return self.alerts
    
    def clear_alerts(self):
        """Limpia las alertas."""
        self.alerts = []
    
    def set_threshold(self, metric: str, value: float):
        """Configura un umbral de alerta."""
        if metric in self.thresholds:
            self.thresholds[metric] = value


def print_bar(percent: float, width: int = 30) -> str:
    """Genera una barra de progreso ASCII."""
    filled = int(width * percent / 100)
    bar = "█" * filled + "░" * (width - filled)
    color = "🟢" if percent < 70 else "🟡" if percent < 85 else "🔴"
    return f"{color} [{bar}] {percent:.1f}%"


def display_dashboard(monitor: SystemMonitor):
    """Muestra un dashboard en tiempo real."""
    try:
        while True:
            os.system('cls' if os.name == 'nt' else 'clear')
            
            print("=" * 70)
            print("  🖥️  MONITOR DEL SISTEMA - Dashboard en Tiempo Real")
            print("=" * 70)
            print(f"  Actualizado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print("=" * 70)
            
            # Información del sistema
            sys_info = monitor.get_system_info()
            print(f"\n  📌 Sistema: {sys_info['os']} ({sys_info['architecture']})")
            print(f"  📌 Host: {sys_info['hostname']}")
            if "uptime_hours" in sys_info:
                print(f"  📌 Uptime: {sys_info['uptime_hours']:.1f} horas")
            
            # CPU
            print("\n  ─────────────────────────────────────────────────────────────")
            cpu = monitor.get_cpu_stats()
            if "error" not in cpu:
                print(f"  🔲 CPU")
                print(f"     Uso total:    {print_bar(cpu['percent_usage'])}")
                print(f"     Núcleos: {cpu['cores_physical']} físicos / {cpu['cores_logical']} lógicos")
                if cpu['frequency_mhz']['current'] > 0:
                    print(f"     Frecuencia: {cpu['frequency_mhz']['current']} MHz")
            
            # Memoria
            print("\n  ─────────────────────────────────────────────────────────────")
            mem = monitor.get_memory_stats()
            if "error" not in mem:
                print(f"  💾 MEMORIA RAM")
                print(f"     Uso:          {print_bar(mem['ram']['percent_used'])}")
                print(f"     Usado: {mem['ram']['used_gb']:.1f} GB / {mem['ram']['total_gb']:.1f} GB")
                print(f"     Disponible: {mem['ram']['available_gb']:.1f} GB")
            
            # Disco
            print("\n  ─────────────────────────────────────────────────────────────")
            disk = monitor.get_disk_stats()
            if "error" not in disk:
                print(f"  💿 DISCO")
                for part in disk['partitions'][:3]:  # Mostrar máximo 3 particiones
                    print(f"     {part['mountpoint']}: {print_bar(part['percent_used'])}")
                    print(f"        Libre: {part['free_gb']:.1f} GB de {part['total_gb']:.1f} GB")
            
            # Red
            print("\n  ─────────────────────────────────────────────────────────────")
            net = monitor.get_network_stats()
            if "error" not in net:
                print(f"  🌐 RED")
                print(f"     Enviado: {net['io']['bytes_sent_gb']:.2f} GB")
                print(f"     Recibido: {net['io']['bytes_recv_gb']:.2f} GB")
                print(f"     Conexiones activas: {net['total_connections']}")
            
            # Top procesos
            print("\n  ─────────────────────────────────────────────────────────────")
            print(f"  📊 TOP 5 PROCESOS (por memoria)")
            processes = monitor.get_process_list(5, "memory")
            print(f"     {'PID':>7}  {'NOMBRE':<25}  {'CPU%':>6}  {'MEM%':>6}")
            for proc in processes:
                print(f"     {proc['pid']:>7}  {proc['name'][:25]:<25}  {proc['cpu_percent']:>5.1f}%  {proc['memory_percent']:>5.1f}%")
            
            # Alertas
            alerts = monitor.get_alerts()
            if alerts:
                print("\n  ─────────────────────────────────────────────────────────────")
                print(f"  ⚠️  ALERTAS ({len(alerts)})")
                for alert in alerts[-3:]:
                    print(f"     [{alert['category']}] {alert['message']}")
            
            print("\n" + "=" * 70)
            print("  Presione Ctrl+C para salir")
            print("=" * 70)
            
            monitor.clear_alerts()
            time.sleep(2)
            
    except KeyboardInterrupt:
        print("\n\n  Monitor detenido.")


def print_single_report(monitor: SystemMonitor):
    """Imprime un reporte único del sistema."""
    print("\n" + "=" * 60)
    print("  REPORTE DEL SISTEMA")
    print("=" * 60)
    
    sys_info = monitor.get_system_info()
    print(f"\n  Sistema: {sys_info['os']} {sys_info['os_version']}")
    print(f"  Host: {sys_info['hostname']}")
    print(f"  Arquitectura: {sys_info['architecture']}")
    
    cpu = monitor.get_cpu_stats()
    if "error" not in cpu:
        print(f"\n  CPU: {cpu['percent_usage']}% en uso")
        print(f"  Núcleos: {cpu['cores_logical']}")
    
    mem = monitor.get_memory_stats()
    if "error" not in mem:
        print(f"\n  RAM: {mem['ram']['percent_used']}% en uso")
        print(f"  Total: {mem['ram']['total_gb']} GB")
    
    disk = monitor.get_disk_stats()
    if "error" not in disk:
        print("\n  Discos:")
        for part in disk['partitions']:
            print(f"    {part['mountpoint']}: {part['percent_used']}% ({part['free_gb']} GB libres)")
    
    print("\n" + "=" * 60)


if __name__ == "__main__":
    if not PSUTIL_AVAILABLE:
        print("\n[ERROR] Este módulo requiere psutil.")
        print("Instálelo ejecutando: pip install psutil")
        exit(1)
    
    monitor = SystemMonitor()
    
    print("\n" + "=" * 60)
    print("  Monitor del Sistema")
    print("=" * 60)
    print("\nOpciones:")
    print("1. Dashboard en tiempo real")
    print("2. Reporte único")
    print("3. Ver procesos (top 15)")
    
    opcion = input("\nSeleccione una opción (1-3): ").strip()
    
    if opcion == "1":
        display_dashboard(monitor)
    elif opcion == "2":
        print_single_report(monitor)
    elif opcion == "3":
        print("\n  Top 15 procesos por uso de memoria:\n")
        processes = monitor.get_process_list(15, "memory")
        print(f"  {'PID':>7}  {'NOMBRE':<30}  {'USUARIO':<15}  {'CPU%':>6}  {'MEM%':>6}")
        print("  " + "-" * 75)
        for proc in processes:
            user = (proc['user'] or 'N/A')[:15]
            print(f"  {proc['pid']:>7}  {proc['name'][:30]:<30}  {user:<15}  {proc['cpu_percent']:>5.1f}%  {proc['memory_percent']:>5.1f}%")
    else:
        print("Opción no válida")
