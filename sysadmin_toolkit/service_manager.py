"""
Gestor de Servicios - Herramienta para administrar servicios del sistema
"""
import platform
import subprocess
from typing import Dict, List, Optional


class ServiceManager:
    """Administrador de servicios del sistema operativo."""
    
    def __init__(self):
        self.system = platform.system().lower()
        self.is_windows = self.system == "windows"
        self.is_linux = self.system == "linux"
        self.is_mac = self.system == "darwin"
    
    def _run_command(self, cmd: List[str], timeout: int = 30) -> Dict:
        """Ejecuta un comando y retorna el resultado."""
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            return {
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode
            }
        except subprocess.TimeoutExpired:
            return {"success": False, "error": "Timeout"}
        except FileNotFoundError:
            return {"success": False, "error": "Comando no encontrado"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def list_services(self, filter_running: Optional[bool] = None) -> List[Dict]:
        """
        Lista los servicios del sistema.
        
        Args:
            filter_running: True para solo activos, False para inactivos, None para todos
        
        Returns:
            Lista de diccionarios con información de servicios
        """
        services = []
        
        if self.is_windows:
            services = self._list_services_windows()
        elif self.is_linux:
            services = self._list_services_linux()
        elif self.is_mac:
            services = self._list_services_mac()
        
        if filter_running is not None:
            if filter_running:
                services = [s for s in services if s.get("status") == "running"]
            else:
                services = [s for s in services if s.get("status") != "running"]
        
        return services
    
    def _list_services_windows(self) -> List[Dict]:
        """Lista servicios en Windows usando PowerShell."""
        cmd = [
            "powershell", "-Command",
            "Get-Service | Select-Object Name, DisplayName, Status, StartType | ConvertTo-Json"
        ]
        
        result = self._run_command(cmd)
        if not result["success"]:
            return []
        
        try:
            import json
            data = json.loads(result["stdout"])
            
            # Asegurar que sea una lista
            if isinstance(data, dict):
                data = [data]
            
            services = []
            for svc in data:
                status_map = {0: "stopped", 1: "stopped", 2: "starting", 
                             3: "stopping", 4: "running"}
                start_map = {0: "boot", 1: "system", 2: "automatic", 
                            3: "manual", 4: "disabled"}
                
                services.append({
                    "name": svc.get("Name", ""),
                    "display_name": svc.get("DisplayName", ""),
                    "status": status_map.get(svc.get("Status"), "unknown"),
                    "start_type": start_map.get(svc.get("StartType"), "unknown")
                })
            
            return services
        except Exception:
            return []
    
    def _list_services_linux(self) -> List[Dict]:
        """Lista servicios en Linux usando systemctl."""
        cmd = ["systemctl", "list-units", "--type=service", "--all", "--no-pager", "--plain"]
        
        result = self._run_command(cmd)
        if not result["success"]:
            return []
        
        services = []
        lines = result["stdout"].strip().split('\n')
        
        for line in lines[1:]:  # Saltar encabezado
            parts = line.split()
            if len(parts) >= 4:
                name = parts[0].replace(".service", "")
                load = parts[1]
                active = parts[2]
                sub = parts[3]
                
                services.append({
                    "name": name,
                    "display_name": name,
                    "status": "running" if sub == "running" else active,
                    "load_state": load
                })
        
        return services
    
    def _list_services_mac(self) -> List[Dict]:
        """Lista servicios en macOS usando launchctl."""
        cmd = ["launchctl", "list"]
        
        result = self._run_command(cmd)
        if not result["success"]:
            return []
        
        services = []
        lines = result["stdout"].strip().split('\n')
        
        for line in lines[1:]:  # Saltar encabezado
            parts = line.split('\t')
            if len(parts) >= 3:
                pid = parts[0]
                status = parts[1]
                name = parts[2]
                
                is_running = pid != "-" and pid.isdigit()
                
                services.append({
                    "name": name,
                    "display_name": name,
                    "status": "running" if is_running else "stopped",
                    "pid": pid if is_running else None
                })
        
        return services
    
    def get_service_status(self, service_name: str) -> Dict:
        """
        Obtiene el estado de un servicio específico.
        
        Args:
            service_name: Nombre del servicio
        
        Returns:
            Diccionario con información del servicio
        """
        if self.is_windows:
            return self._get_service_windows(service_name)
        elif self.is_linux:
            return self._get_service_linux(service_name)
        elif self.is_mac:
            return self._get_service_mac(service_name)
        
        return {"error": "Sistema operativo no soportado"}
    
    def _get_service_windows(self, name: str) -> Dict:
        """Obtiene estado de servicio en Windows."""
        cmd = [
            "powershell", "-Command",
            f"Get-Service -Name '{name}' | Select-Object Name, DisplayName, Status, StartType | ConvertTo-Json"
        ]
        
        result = self._run_command(cmd)
        if not result["success"]:
            return {"error": f"Servicio no encontrado: {name}"}
        
        try:
            import json
            data = json.loads(result["stdout"])
            
            status_map = {0: "stopped", 1: "stopped", 2: "starting", 
                         3: "stopping", 4: "running"}
            
            return {
                "name": data.get("Name"),
                "display_name": data.get("DisplayName"),
                "status": status_map.get(data.get("Status"), "unknown"),
                "running": data.get("Status") == 4
            }
        except Exception as e:
            return {"error": str(e)}
    
    def _get_service_linux(self, name: str) -> Dict:
        """Obtiene estado de servicio en Linux."""
        cmd = ["systemctl", "status", name, "--no-pager"]
        
        result = self._run_command(cmd)
        
        # systemctl status retorna 3 si el servicio está inactivo
        is_running = "Active: active (running)" in result["stdout"]
        is_enabled = "enabled;" in result["stdout"]
        
        return {
            "name": name,
            "display_name": name,
            "status": "running" if is_running else "stopped",
            "running": is_running,
            "enabled": is_enabled,
            "details": result["stdout"][:500] if result["stdout"] else ""
        }
    
    def _get_service_mac(self, name: str) -> Dict:
        """Obtiene estado de servicio en macOS."""
        cmd = ["launchctl", "list", name]
        
        result = self._run_command(cmd)
        
        return {
            "name": name,
            "running": result["success"],
            "status": "running" if result["success"] else "stopped"
        }
    
    def start_service(self, service_name: str) -> Dict:
        """
        Inicia un servicio.
        
        Args:
            service_name: Nombre del servicio
        
        Returns:
            Diccionario con resultado de la operación
        """
        if self.is_windows:
            cmd = ["powershell", "-Command", f"Start-Service -Name '{service_name}'"]
        elif self.is_linux:
            cmd = ["sudo", "systemctl", "start", service_name]
        elif self.is_mac:
            cmd = ["sudo", "launchctl", "start", service_name]
        else:
            return {"success": False, "error": "SO no soportado"}
        
        result = self._run_command(cmd)
        
        if result["success"]:
            return {"success": True, "message": f"Servicio {service_name} iniciado"}
        else:
            return {"success": False, "error": result.get("stderr") or result.get("error")}
    
    def stop_service(self, service_name: str) -> Dict:
        """
        Detiene un servicio.
        
        Args:
            service_name: Nombre del servicio
        
        Returns:
            Diccionario con resultado de la operación
        """
        if self.is_windows:
            cmd = ["powershell", "-Command", f"Stop-Service -Name '{service_name}' -Force"]
        elif self.is_linux:
            cmd = ["sudo", "systemctl", "stop", service_name]
        elif self.is_mac:
            cmd = ["sudo", "launchctl", "stop", service_name]
        else:
            return {"success": False, "error": "SO no soportado"}
        
        result = self._run_command(cmd)
        
        if result["success"]:
            return {"success": True, "message": f"Servicio {service_name} detenido"}
        else:
            return {"success": False, "error": result.get("stderr") or result.get("error")}
    
    def restart_service(self, service_name: str) -> Dict:
        """
        Reinicia un servicio.
        
        Args:
            service_name: Nombre del servicio
        
        Returns:
            Diccionario con resultado de la operación
        """
        if self.is_windows:
            cmd = ["powershell", "-Command", f"Restart-Service -Name '{service_name}' -Force"]
        elif self.is_linux:
            cmd = ["sudo", "systemctl", "restart", service_name]
        elif self.is_mac:
            # macOS no tiene restart directo
            self.stop_service(service_name)
            return self.start_service(service_name)
        else:
            return {"success": False, "error": "SO no soportado"}
        
        result = self._run_command(cmd)
        
        if result["success"]:
            return {"success": True, "message": f"Servicio {service_name} reiniciado"}
        else:
            return {"success": False, "error": result.get("stderr") or result.get("error")}
    
    def enable_service(self, service_name: str) -> Dict:
        """Habilita un servicio para inicio automático (Linux/Windows)."""
        if self.is_windows:
            cmd = ["powershell", "-Command", 
                   f"Set-Service -Name '{service_name}' -StartupType Automatic"]
        elif self.is_linux:
            cmd = ["sudo", "systemctl", "enable", service_name]
        else:
            return {"success": False, "error": "No soportado en este SO"}
        
        result = self._run_command(cmd)
        
        if result["success"]:
            return {"success": True, "message": f"Servicio {service_name} habilitado"}
        else:
            return {"success": False, "error": result.get("stderr") or result.get("error")}
    
    def disable_service(self, service_name: str) -> Dict:
        """Deshabilita un servicio del inicio automático (Linux/Windows)."""
        if self.is_windows:
            cmd = ["powershell", "-Command", 
                   f"Set-Service -Name '{service_name}' -StartupType Manual"]
        elif self.is_linux:
            cmd = ["sudo", "systemctl", "disable", service_name]
        else:
            return {"success": False, "error": "No soportado en este SO"}
        
        result = self._run_command(cmd)
        
        if result["success"]:
            return {"success": True, "message": f"Servicio {service_name} deshabilitado"}
        else:
            return {"success": False, "error": result.get("stderr") or result.get("error")}
    
    def search_services(self, keyword: str) -> List[Dict]:
        """
        Busca servicios por nombre.
        
        Args:
            keyword: Palabra clave a buscar
        
        Returns:
            Lista de servicios que coinciden
        """
        all_services = self.list_services()
        keyword_lower = keyword.lower()
        
        return [
            svc for svc in all_services 
            if keyword_lower in svc.get("name", "").lower() 
            or keyword_lower in svc.get("display_name", "").lower()
        ]


def run_service_manager():
    """Ejecuta el gestor de servicios interactivo."""
    manager = ServiceManager()
    
    print(f"\n  Sistema detectado: {manager.system.capitalize()}")
    
    while True:
        print("\n" + "="*60)
        print("  GESTOR DE SERVICIOS")
        print("="*60)
        print("\n  Opciones:")
        print("  1. Listar servicios activos")
        print("  2. Listar todos los servicios")
        print("  3. Buscar servicio")
        print("  4. Ver estado de un servicio")
        print("  5. Iniciar servicio")
        print("  6. Detener servicio")
        print("  7. Reiniciar servicio")
        print("  8. Habilitar/Deshabilitar servicio")
        print("  9. Volver")
        
        opcion = input("\n  Seleccione (1-9): ").strip()
        
        if opcion == "1":
            print("\n  Obteniendo servicios activos...")
            services = manager.list_services(filter_running=True)
            
            print(f"\n  Servicios activos: {len(services)}")
            print(f"\n  {'NOMBRE':<35} {'DESCRIPCIÓN':<40}")
            print("  " + "-"*75)
            
            for svc in services[:30]:
                name = svc.get("name", "")[:35]
                display = svc.get("display_name", "")[:40]
                print(f"  {name:<35} {display:<40}")
            
            if len(services) > 30:
                print(f"\n  ... y {len(services) - 30} servicios más")
        
        elif opcion == "2":
            print("\n  Obteniendo todos los servicios...")
            services = manager.list_services()
            
            running = len([s for s in services if s.get("status") == "running"])
            
            print(f"\n  Total: {len(services)} | Activos: {running} | Inactivos: {len(services) - running}")
            print(f"\n  {'NOMBRE':<30} {'ESTADO':<12} {'TIPO INICIO'}")
            print("  " + "-"*60)
            
            for svc in services[:40]:
                name = svc.get("name", "")[:30]
                status = svc.get("status", "unknown")
                start_type = svc.get("start_type", "")
                
                status_icon = "●" if status == "running" else "○"
                print(f"  {name:<30} {status_icon} {status:<10} {start_type}")
            
            if len(services) > 40:
                print(f"\n  ... y {len(services) - 40} servicios más")
        
        elif opcion == "3":
            keyword = input("  Buscar: ").strip()
            
            if keyword:
                results = manager.search_services(keyword)
                
                print(f"\n  Encontrados: {len(results)} servicios")
                for svc in results[:20]:
                    status = svc.get("status", "unknown")
                    status_icon = "●" if status == "running" else "○"
                    print(f"  {status_icon} {svc.get('name')} - {svc.get('display_name', '')[:40]}")
        
        elif opcion == "4":
            name = input("  Nombre del servicio: ").strip()
            
            if name:
                status = manager.get_service_status(name)
                
                if "error" in status:
                    print(f"\n  Error: {status['error']}")
                else:
                    print(f"\n  Servicio: {status.get('name')}")
                    print(f"  Descripción: {status.get('display_name', 'N/A')}")
                    print(f"  Estado: {status.get('status')}")
                    print(f"  En ejecución: {'Sí' if status.get('running') else 'No'}")
        
        elif opcion == "5":
            name = input("  Servicio a iniciar: ").strip()
            
            if name:
                print("\n  Iniciando servicio...")
                result = manager.start_service(name)
                
                if result["success"]:
                    print(f"  ✓ {result['message']}")
                else:
                    print(f"  ✗ Error: {result.get('error')}")
        
        elif opcion == "6":
            name = input("  Servicio a detener: ").strip()
            
            if name:
                confirm = input(f"  ¿Detener {name}? (s/n): ").strip().lower()
                
                if confirm == 's':
                    print("\n  Deteniendo servicio...")
                    result = manager.stop_service(name)
                    
                    if result["success"]:
                        print(f"  ✓ {result['message']}")
                    else:
                        print(f"  ✗ Error: {result.get('error')}")
        
        elif opcion == "7":
            name = input("  Servicio a reiniciar: ").strip()
            
            if name:
                print("\n  Reiniciando servicio...")
                result = manager.restart_service(name)
                
                if result["success"]:
                    print(f"  ✓ {result['message']}")
                else:
                    print(f"  ✗ Error: {result.get('error')}")
        
        elif opcion == "8":
            name = input("  Nombre del servicio: ").strip()
            
            if name:
                print("  1. Habilitar (inicio automático)")
                print("  2. Deshabilitar (inicio manual)")
                action = input("  Seleccione: ").strip()
                
                if action == "1":
                    result = manager.enable_service(name)
                elif action == "2":
                    result = manager.disable_service(name)
                else:
                    continue
                
                if result["success"]:
                    print(f"  ✓ {result['message']}")
                else:
                    print(f"  ✗ Error: {result.get('error')}")
        
        elif opcion == "9":
            break


if __name__ == "__main__":
    run_service_manager()
