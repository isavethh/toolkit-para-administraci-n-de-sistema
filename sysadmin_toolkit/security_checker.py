"""
Verificador de Seguridad - Herramienta para auditar configuraciones de seguridad básicas
"""
import os
import platform
import socket
import subprocess
import hashlib
import re
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional


class SecurityChecker:
    """Verificador de configuraciones de seguridad del sistema."""
    
    def __init__(self):
        self.system = platform.system().lower()
        self.is_windows = self.system == "windows"
        self.is_linux = self.system == "linux"
        self.findings = []
    
    def _add_finding(self, category: str, severity: str, title: str, 
                     description: str, recommendation: str = ""):
        """Agrega un hallazgo de seguridad."""
        self.findings.append({
            "category": category,
            "severity": severity,  # "critical", "high", "medium", "low", "info"
            "title": title,
            "description": description,
            "recommendation": recommendation,
            "timestamp": datetime.now().isoformat()
        })
    
    def _run_command(self, cmd: List[str], timeout: int = 30) -> Dict:
        """Ejecuta un comando y retorna el resultado."""
        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=timeout
            )
            return {
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def run_full_audit(self) -> Dict:
        """
        Ejecuta una auditoría completa del sistema.
        
        Returns:
            Diccionario con resultados de la auditoría
        """
        self.findings = []
        
        # Ejecutar todas las verificaciones
        self.check_open_ports()
        self.check_firewall_status()
        self.check_password_policy()
        self.check_user_accounts()
        self.check_updates()
        self.check_antivirus()
        self.check_shared_folders()
        self.check_startup_programs()
        self.check_suspicious_connections()
        
        # Generar resumen
        summary = {
            "total_findings": len(self.findings),
            "by_severity": {
                "critical": len([f for f in self.findings if f["severity"] == "critical"]),
                "high": len([f for f in self.findings if f["severity"] == "high"]),
                "medium": len([f for f in self.findings if f["severity"] == "medium"]),
                "low": len([f for f in self.findings if f["severity"] == "low"]),
                "info": len([f for f in self.findings if f["severity"] == "info"])
            },
            "findings": self.findings,
            "audit_date": datetime.now().isoformat(),
            "system": self.system
        }
        
        return summary
    
    def check_open_ports(self) -> List[Dict]:
        """Verifica puertos abiertos en escucha."""
        open_ports = []
        
        try:
            if self.is_windows:
                result = self._run_command(["netstat", "-ano"])
            else:
                result = self._run_command(["netstat", "-tlnp"])
            
            if result["success"]:
                lines = result["stdout"].split('\n')
                
                for line in lines:
                    if "LISTEN" in line or "ESCUCHANDO" in line:
                        # Extraer puerto
                        match = re.search(r':(\d+)\s', line)
                        if match:
                            port = int(match.group(1))
                            open_ports.append({
                                "port": port,
                                "line": line.strip()
                            })
                
                # Puertos potencialmente peligrosos
                dangerous_ports = {
                    21: "FTP - Protocolo sin cifrado",
                    23: "Telnet - Protocolo sin cifrado",
                    135: "RPC - Objetivo común de ataques",
                    139: "NetBIOS - Riesgo de enumeración",
                    445: "SMB - Objetivo de ransomware",
                    1433: "SQL Server - Base de datos expuesta",
                    3306: "MySQL - Base de datos expuesta",
                    3389: "RDP - Acceso remoto expuesto",
                    5900: "VNC - Escritorio remoto sin cifrado"
                }
                
                for port_info in open_ports:
                    port = port_info["port"]
                    if port in dangerous_ports:
                        self._add_finding(
                            "network",
                            "high" if port in [21, 23, 3389] else "medium",
                            f"Puerto {port} abierto",
                            dangerous_ports[port],
                            f"Considere cerrar el puerto {port} si no es necesario"
                        )
        except Exception as e:
            pass
        
        return open_ports
    
    def check_firewall_status(self) -> Dict:
        """Verifica el estado del firewall."""
        result = {"enabled": False, "profiles": []}
        
        if self.is_windows:
            cmd = ["powershell", "-Command",
                   "Get-NetFirewallProfile | Select-Object Name, Enabled | ConvertTo-Json"]
            
            output = self._run_command(cmd)
            
            if output["success"]:
                try:
                    import json
                    profiles = json.loads(output["stdout"])
                    
                    if isinstance(profiles, dict):
                        profiles = [profiles]
                    
                    all_enabled = True
                    for profile in profiles:
                        is_enabled = profile.get("Enabled", False)
                        result["profiles"].append({
                            "name": profile.get("Name"),
                            "enabled": is_enabled
                        })
                        if not is_enabled:
                            all_enabled = False
                    
                    result["enabled"] = all_enabled
                    
                    if not all_enabled:
                        self._add_finding(
                            "firewall",
                            "critical",
                            "Firewall deshabilitado",
                            "Uno o más perfiles del firewall están deshabilitados",
                            "Habilite el firewall de Windows en todos los perfiles"
                        )
                    else:
                        self._add_finding(
                            "firewall",
                            "info",
                            "Firewall habilitado",
                            "El firewall está activo en todos los perfiles",
                            ""
                        )
                except Exception:
                    pass
        
        elif self.is_linux:
            # Verificar UFW
            ufw_result = self._run_command(["ufw", "status"])
            if ufw_result["success"]:
                if "active" in ufw_result["stdout"].lower():
                    result["enabled"] = True
                    result["type"] = "ufw"
                    self._add_finding("firewall", "info", "UFW activo",
                                     "El firewall UFW está habilitado", "")
                else:
                    self._add_finding("firewall", "high", "UFW inactivo",
                                     "El firewall UFW está deshabilitado",
                                     "Ejecute: sudo ufw enable")
            
            # Verificar iptables
            ipt_result = self._run_command(["iptables", "-L", "-n"])
            if ipt_result["success"]:
                lines = [l for l in ipt_result["stdout"].split('\n') 
                        if l and not l.startswith("Chain") and not l.startswith("target")]
                if len(lines) > 0:
                    result["iptables_rules"] = len(lines)
        
        return result
    
    def check_password_policy(self) -> Dict:
        """Verifica la política de contraseñas."""
        policy = {}
        
        if self.is_windows:
            cmd = ["net", "accounts"]
            result = self._run_command(cmd)
            
            if result["success"]:
                lines = result["stdout"].split('\n')
                
                for line in lines:
                    if ":" in line:
                        key, value = line.split(":", 1)
                        policy[key.strip()] = value.strip()
                
                # Verificar configuraciones
                min_length = policy.get("Minimum password length", "0")
                if min_length.isdigit() and int(min_length) < 8:
                    self._add_finding(
                        "passwords",
                        "high",
                        "Longitud mínima de contraseña débil",
                        f"La longitud mínima es {min_length} caracteres",
                        "Configure una longitud mínima de 12 caracteres"
                    )
                
                max_age = policy.get("Maximum password age (days)", "")
                if "unlimited" in max_age.lower() or max_age == "0":
                    self._add_finding(
                        "passwords",
                        "medium",
                        "Las contraseñas no expiran",
                        "No hay política de expiración de contraseñas",
                        "Configure expiración cada 90 días"
                    )
        
        elif self.is_linux:
            # Verificar /etc/login.defs
            login_defs = Path("/etc/login.defs")
            if login_defs.exists():
                try:
                    content = login_defs.read_text()
                    
                    # Buscar configuraciones
                    for line in content.split('\n'):
                        if line.startswith("PASS_MIN_LEN"):
                            parts = line.split()
                            if len(parts) > 1:
                                min_len = int(parts[1])
                                policy["min_length"] = min_len
                                if min_len < 8:
                                    self._add_finding(
                                        "passwords", "high",
                                        "Longitud mínima débil",
                                        f"PASS_MIN_LEN = {min_len}",
                                        "Aumente a 12 en /etc/login.defs"
                                    )
                except Exception:
                    pass
        
        return policy
    
    def check_user_accounts(self) -> List[Dict]:
        """Verifica cuentas de usuario del sistema."""
        users = []
        
        if self.is_windows:
            cmd = ["powershell", "-Command",
                   "Get-LocalUser | Select-Object Name, Enabled, PasswordRequired, LastLogon | ConvertTo-Json"]
            
            result = self._run_command(cmd)
            
            if result["success"]:
                try:
                    import json
                    data = json.loads(result["stdout"])
                    
                    if isinstance(data, dict):
                        data = [data]
                    
                    for user in data:
                        users.append({
                            "name": user.get("Name"),
                            "enabled": user.get("Enabled"),
                            "password_required": user.get("PasswordRequired")
                        })
                        
                        # Verificar problemas
                        if user.get("Enabled") and not user.get("PasswordRequired"):
                            self._add_finding(
                                "users",
                                "critical",
                                f"Usuario sin contraseña: {user.get('Name')}",
                                "Esta cuenta no requiere contraseña",
                                "Configure una contraseña para esta cuenta"
                            )
                except Exception:
                    pass
        
        elif self.is_linux:
            # Verificar /etc/passwd
            passwd_file = Path("/etc/passwd")
            if passwd_file.exists():
                try:
                    for line in passwd_file.read_text().split('\n'):
                        if line:
                            parts = line.split(':')
                            if len(parts) >= 7:
                                uid = int(parts[2])
                                shell = parts[6]
                                
                                # Solo usuarios con shell válido
                                if "/bin/bash" in shell or "/bin/sh" in shell:
                                    users.append({
                                        "name": parts[0],
                                        "uid": uid,
                                        "home": parts[5],
                                        "shell": shell
                                    })
                                    
                                    # Verificar UID 0 (root)
                                    if uid == 0 and parts[0] != "root":
                                        self._add_finding(
                                            "users", "critical",
                                            f"Usuario con UID 0: {parts[0]}",
                                            "Este usuario tiene privilegios de root",
                                            "Investigue si es legítimo"
                                        )
                except Exception:
                    pass
            
            # Verificar usuarios sin contraseña
            shadow_check = self._run_command(["sudo", "cat", "/etc/shadow"])
            if shadow_check["success"]:
                for line in shadow_check["stdout"].split('\n'):
                    if line:
                        parts = line.split(':')
                        if len(parts) >= 2:
                            username = parts[0]
                            password_hash = parts[1]
                            
                            if password_hash in ["", "!", "!!"]:
                                # Cuenta bloqueada o sin contraseña
                                pass
                            elif password_hash == "*":
                                pass  # Cuenta de sistema
        
        return users
    
    def check_updates(self) -> Dict:
        """Verifica el estado de actualizaciones del sistema."""
        updates = {"available": 0, "last_check": None}
        
        if self.is_windows:
            cmd = ["powershell", "-Command",
                   "(New-Object -ComObject Microsoft.Update.AutoUpdate).Results"]
            
            result = self._run_command(cmd)
            
            # Verificar Windows Update
            cmd2 = ["powershell", "-Command",
                    "Get-HotFix | Sort-Object InstalledOn -Descending | Select-Object -First 1"]
            
            result2 = self._run_command(cmd2)
            
            if result2["success"] and result2["stdout"]:
                # Parsear fecha del último hotfix
                lines = result2["stdout"].split('\n')
                for line in lines:
                    if "/" in line:
                        try:
                            # Intentar extraer fecha
                            updates["last_update"] = line.strip()
                        except Exception:
                            pass
        
        elif self.is_linux:
            # Para sistemas basados en apt
            apt_check = self._run_command(["apt", "list", "--upgradable"])
            
            if apt_check["success"]:
                lines = [l for l in apt_check["stdout"].split('\n') 
                        if l and "Listing" not in l]
                updates["available"] = len(lines)
                
                if len(lines) > 10:
                    self._add_finding(
                        "updates",
                        "medium",
                        f"{len(lines)} actualizaciones pendientes",
                        "Hay actualizaciones de seguridad disponibles",
                        "Ejecute: sudo apt update && sudo apt upgrade"
                    )
        
        return updates
    
    def check_antivirus(self) -> Dict:
        """Verifica el estado del antivirus."""
        av_status = {"installed": False, "name": None, "enabled": False}
        
        if self.is_windows:
            cmd = ["powershell", "-Command",
                   "Get-MpComputerStatus | Select-Object AntivirusEnabled, RealTimeProtectionEnabled, AntivirusSignatureAge | ConvertTo-Json"]
            
            result = self._run_command(cmd)
            
            if result["success"]:
                try:
                    import json
                    data = json.loads(result["stdout"])
                    
                    av_status["installed"] = True
                    av_status["name"] = "Windows Defender"
                    av_status["enabled"] = data.get("AntivirusEnabled", False)
                    av_status["realtime"] = data.get("RealTimeProtectionEnabled", False)
                    av_status["signature_age"] = data.get("AntivirusSignatureAge", 0)
                    
                    if not data.get("RealTimeProtectionEnabled"):
                        self._add_finding(
                            "antivirus",
                            "critical",
                            "Protección en tiempo real deshabilitada",
                            "Windows Defender no está protegiendo activamente",
                            "Habilite la protección en tiempo real"
                        )
                    
                    sig_age = data.get("AntivirusSignatureAge", 0)
                    if sig_age > 7:
                        self._add_finding(
                            "antivirus",
                            "high",
                            "Firmas de antivirus desactualizadas",
                            f"Las firmas tienen {sig_age} días de antigüedad",
                            "Actualice las definiciones de virus"
                        )
                except Exception:
                    pass
        
        return av_status
    
    def check_shared_folders(self) -> List[Dict]:
        """Verifica carpetas compartidas."""
        shares = []
        
        if self.is_windows:
            cmd = ["powershell", "-Command",
                   "Get-SmbShare | Select-Object Name, Path, Description | ConvertTo-Json"]
            
            result = self._run_command(cmd)
            
            if result["success"]:
                try:
                    import json
                    data = json.loads(result["stdout"])
                    
                    if isinstance(data, dict):
                        data = [data]
                    
                    for share in data:
                        name = share.get("Name", "")
                        
                        # Ignorar compartidos del sistema
                        if name.endswith("$"):
                            continue
                        
                        shares.append({
                            "name": name,
                            "path": share.get("Path"),
                            "description": share.get("Description")
                        })
                        
                        self._add_finding(
                            "shares",
                            "info",
                            f"Carpeta compartida: {name}",
                            f"Ruta: {share.get('Path')}",
                            "Verifique los permisos de acceso"
                        )
                except Exception:
                    pass
        
        return shares
    
    def check_startup_programs(self) -> List[Dict]:
        """Verifica programas de inicio."""
        startup = []
        
        if self.is_windows:
            cmd = ["powershell", "-Command",
                   "Get-CimInstance Win32_StartupCommand | Select-Object Name, Command, Location | ConvertTo-Json"]
            
            result = self._run_command(cmd)
            
            if result["success"]:
                try:
                    import json
                    data = json.loads(result["stdout"])
                    
                    if isinstance(data, dict):
                        data = [data]
                    
                    for item in data:
                        startup.append({
                            "name": item.get("Name"),
                            "command": item.get("Command"),
                            "location": item.get("Location")
                        })
                    
                    if len(data) > 15:
                        self._add_finding(
                            "startup",
                            "low",
                            f"{len(data)} programas en el inicio",
                            "Muchos programas pueden afectar el rendimiento",
                            "Revise y deshabilite los innecesarios"
                        )
                except Exception:
                    pass
        
        return startup
    
    def check_suspicious_connections(self) -> List[Dict]:
        """Verifica conexiones de red sospechosas."""
        suspicious = []
        
        if self.is_windows:
            cmd = ["netstat", "-ano"]
        else:
            cmd = ["netstat", "-tunp"]
        
        result = self._run_command(cmd)
        
        if result["success"]:
            lines = result["stdout"].split('\n')
            
            # Puertos de destino sospechosos
            suspicious_ports = [4444, 5555, 6666, 31337, 12345, 54321]
            
            for line in lines:
                if "ESTABLISHED" in line or "CONECTADO" in line:
                    for port in suspicious_ports:
                        if f":{port}" in line:
                            suspicious.append({
                                "connection": line.strip(),
                                "suspicious_port": port
                            })
                            
                            self._add_finding(
                                "network",
                                "critical",
                                f"Conexión sospechosa al puerto {port}",
                                line.strip(),
                                "Investigue esta conexión inmediatamente"
                            )
        
        return suspicious
    
    def check_file_integrity(self, file_path: str) -> Dict:
        """
        Calcula el hash de un archivo para verificación de integridad.
        
        Args:
            file_path: Ruta del archivo
        
        Returns:
            Diccionario con hashes del archivo
        """
        path = Path(file_path)
        
        if not path.exists():
            return {"error": "Archivo no encontrado"}
        
        try:
            with open(path, 'rb') as f:
                content = f.read()
            
            return {
                "file": file_path,
                "size": len(content),
                "md5": hashlib.md5(content).hexdigest(),
                "sha256": hashlib.sha256(content).hexdigest()
            }
        except Exception as e:
            return {"error": str(e)}
    
    def generate_report(self, output_format: str = "text") -> str:
        """
        Genera un reporte de la auditoría.
        
        Args:
            output_format: Formato del reporte ("text" o "json")
        
        Returns:
            Reporte como string
        """
        if output_format == "json":
            import json
            return json.dumps({
                "findings": self.findings,
                "generated": datetime.now().isoformat()
            }, indent=2)
        
        # Formato texto
        report = []
        report.append("=" * 70)
        report.append("  REPORTE DE AUDITORÍA DE SEGURIDAD")
        report.append("=" * 70)
        report.append(f"  Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"  Sistema: {platform.system()} {platform.release()}")
        report.append(f"  Total de hallazgos: {len(self.findings)}")
        report.append("")
        
        # Agrupar por severidad
        for severity in ["critical", "high", "medium", "low", "info"]:
            findings = [f for f in self.findings if f["severity"] == severity]
            
            if findings:
                icon = {"critical": "🔴", "high": "🟠", "medium": "🟡", 
                       "low": "🔵", "info": "⚪"}.get(severity, "")
                
                report.append(f"\n  {icon} {severity.upper()} ({len(findings)})")
                report.append("  " + "-" * 50)
                
                for f in findings:
                    report.append(f"  • {f['title']}")
                    report.append(f"    {f['description']}")
                    if f["recommendation"]:
                        report.append(f"    → {f['recommendation']}")
                    report.append("")
        
        report.append("=" * 70)
        return "\n".join(report)


def run_security_checker():
    """Ejecuta el verificador de seguridad interactivo."""
    checker = SecurityChecker()
    
    while True:
        print("\n" + "="*60)
        print("  VERIFICADOR DE SEGURIDAD")
        print("="*60)
        print("\n  Opciones:")
        print("  1. Auditoría completa")
        print("  2. Verificar puertos abiertos")
        print("  3. Verificar firewall")
        print("  4. Verificar cuentas de usuario")
        print("  5. Verificar antivirus")
        print("  6. Verificar conexiones de red")
        print("  7. Calcular hash de archivo")
        print("  8. Ver último reporte")
        print("  9. Volver")
        
        opcion = input("\n  Seleccione (1-9): ").strip()
        
        if opcion == "1":
            print("\n  Ejecutando auditoría completa...")
            print("  Esto puede tardar unos segundos...\n")
            
            results = checker.run_full_audit()
            
            print(f"  Auditoría completada")
            print(f"\n  Hallazgos por severidad:")
            print(f"    🔴 Críticos:  {results['by_severity']['critical']}")
            print(f"    🟠 Altos:     {results['by_severity']['high']}")
            print(f"    🟡 Medios:    {results['by_severity']['medium']}")
            print(f"    🔵 Bajos:     {results['by_severity']['low']}")
            print(f"    ⚪ Info:      {results['by_severity']['info']}")
            
            ver_detalle = input("\n  ¿Ver reporte completo? (s/n): ").strip().lower()
            if ver_detalle == 's':
                print(checker.generate_report())
        
        elif opcion == "2":
            print("\n  Escaneando puertos...")
            ports = checker.check_open_ports()
            
            print(f"\n  Puertos en escucha: {len(ports)}")
            for p in ports[:20]:
                print(f"    Puerto {p['port']}")
        
        elif opcion == "3":
            print("\n  Verificando firewall...")
            status = checker.check_firewall_status()
            
            if status["enabled"]:
                print("\n  ✓ Firewall HABILITADO")
            else:
                print("\n  ✗ Firewall DESHABILITADO")
            
            for profile in status.get("profiles", []):
                status_icon = "✓" if profile.get("enabled") else "✗"
                print(f"    {status_icon} {profile.get('name')}")
        
        elif opcion == "4":
            print("\n  Verificando cuentas...")
            users = checker.check_user_accounts()
            
            print(f"\n  Cuentas encontradas: {len(users)}")
            for u in users[:15]:
                status = "●" if u.get("enabled") else "○"
                print(f"    {status} {u.get('name')}")
        
        elif opcion == "5":
            print("\n  Verificando antivirus...")
            av = checker.check_antivirus()
            
            if av.get("installed"):
                print(f"\n  Antivirus: {av.get('name')}")
                print(f"  Habilitado: {'Sí' if av.get('enabled') else 'No'}")
                print(f"  Tiempo real: {'Sí' if av.get('realtime') else 'No'}")
                if av.get("signature_age"):
                    print(f"  Antigüedad de firmas: {av['signature_age']} días")
            else:
                print("\n  ⚠ No se detectó antivirus")
        
        elif opcion == "6":
            print("\n  Verificando conexiones...")
            suspicious = checker.check_suspicious_connections()
            
            if suspicious:
                print(f"\n  ⚠ Conexiones sospechosas: {len(suspicious)}")
                for s in suspicious:
                    print(f"    Puerto {s['suspicious_port']}: {s['connection'][:50]}")
            else:
                print("\n  ✓ No se detectaron conexiones sospechosas")
        
        elif opcion == "7":
            file_path = input("  Ruta del archivo: ").strip()
            
            if file_path:
                result = checker.check_file_integrity(file_path)
                
                if "error" in result:
                    print(f"\n  Error: {result['error']}")
                else:
                    print(f"\n  Archivo: {result['file']}")
                    print(f"  Tamaño: {result['size']} bytes")
                    print(f"  MD5:    {result['md5']}")
                    print(f"  SHA256: {result['sha256']}")
        
        elif opcion == "8":
            if checker.findings:
                print(checker.generate_report())
            else:
                print("\n  No hay auditoría previa. Ejecute la opción 1 primero.")
        
        elif opcion == "9":
            break


if __name__ == "__main__":
    run_security_checker()
