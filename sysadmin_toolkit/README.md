# SysAdmin Toolkit

Conjunto de herramientas de línea de comandos para administración de sistemas, desarrollado en Python. Permite realizar tareas comunes de diagnóstico, monitoreo, mantenimiento y seguridad en servidores y estaciones de trabajo.

## Contenido

- [Requisitos](#requisitos)
- [Instalación](#instalación)
- [Módulos](#módulos)
- [Uso](#uso)
- [Ejemplos](#ejemplos)
- [Estructura del proyecto](#estructura-del-proyecto)

## Requisitos

- Python 3.7 o superior
- Sistema operativo: Windows, Linux o macOS
- Permisos de administrador (para algunas funciones)

## Instalación

```bash
cd sysadmin_toolkit
pip install -r requirements.txt
```

## Módulos

### 1. Escáner de Puertos (`port_scanner.py`)

Detecta puertos abiertos en un host local o remoto mediante conexiones TCP.

- Escaneo rápido de puertos comunes (22, 80, 443, etc.)
- Escaneo de rangos personalizados
- Ejecución multi-hilo para mayor velocidad
- Identificación automática de servicios

### 2. Parser de Logs (`log_parser.py`)

Analiza archivos de registro del sistema para extraer información relevante.

- Soporte para formatos: syslog, Apache, nginx, Windows Event
- Detección automática del formato
- Filtrado por nivel de severidad (ERROR, WARNING, INFO)
- Búsqueda por palabras clave y expresiones regulares
- Generación de reportes y estadísticas

### 3. Monitor del Sistema (`system_monitor.py`)

Muestra el estado actual de los recursos del equipo.

- Uso de CPU (porcentaje, núcleos, frecuencia)
- Memoria RAM y swap
- Espacio en disco por partición
- Tráfico de red y conexiones activas
- Lista de procesos ordenados por consumo
- Dashboard en tiempo real
- Alertas configurables por umbrales

### 4. Utilidades de Red (`network_utils.py`)

Herramientas para diagnóstico de conectividad de red.

- Ping a hosts con estadísticas de latencia
- Traceroute con tiempos por salto
- Búsqueda DNS directa e inversa
- Verificación de disponibilidad de múltiples hosts
- Detección de IP local y pública
- Comprobación de puertos específicos

### 5. Gestor de Backups (`backup_manager.py`)

Crea y administra copias de seguridad de archivos y directorios.

- Compresión en formato ZIP o TAR.GZ
- Exclusión de patrones (ej: `__pycache__`, `.git`)
- Restauración de backups
- Verificación de integridad mediante hash MD5
- Registro de backups en manifiesto JSON
- Estadísticas de espacio utilizado

### 6. Limpiador de Disco (`disk_cleaner.py`)

Libera espacio eliminando archivos temporales y basura del sistema.

- Escaneo de carpetas temporales del sistema
- Búsqueda de archivos antiguos por fecha
- Detección de archivos grandes
- Búsqueda de archivos duplicados
- Vista de uso de disco por partición
- Vaciado de papelera de reciclaje

### 7. Gestor de Servicios (`service_manager.py`)

Administra servicios del sistema operativo.

- Listar servicios activos e inactivos
- Buscar servicios por nombre
- Iniciar, detener y reiniciar servicios
- Habilitar/deshabilitar inicio automático
- Compatible con Windows (SC), Linux (systemd) y macOS (launchctl)

### 8. Verificador de Seguridad (`security_checker.py`)

Audita configuraciones de seguridad básicas del sistema.

- Detección de puertos peligrosos abiertos
- Verificación del estado del firewall
- Análisis de política de contraseñas
- Revisión de cuentas de usuario
- Estado del antivirus (Windows Defender)
- Detección de conexiones sospechosas
- Verificación de integridad de archivos (hash)
- Generación de reportes de auditoría

## Uso

### Menú interactivo

```bash
python main.py
```

Abre un menú donde puede seleccionar la herramienta que necesita.

### Ejecución individual de módulos

```bash
python port_scanner.py
python log_parser.py
python system_monitor.py
python network_utils.py
python backup_manager.py
python disk_cleaner.py
python service_manager.py
python security_checker.py
```

## Ejemplos

### Escanear puertos

```python
from port_scanner import scan_ports, quick_scan

quick_scan("192.168.1.1")
scan_ports("192.168.1.1", start_port=1, end_port=1000)
```

### Analizar logs

```python
from log_parser import LogParser

parser = LogParser()
parser.parse_file("/var/log/syslog")
errores = parser.filter_by_level("ERROR")
print(parser.get_summary())
```

### Monitorear sistema

```python
from system_monitor import SystemMonitor

monitor = SystemMonitor()
print(f"CPU: {monitor.get_cpu_stats()['percent_usage']}%")
print(f"RAM: {monitor.get_memory_stats()['ram']['percent_used']}%")
```

### Diagnóstico de red

```python
from network_utils import NetworkUtils

utils = NetworkUtils()
resultado = utils.ping("google.com", count=4)
print(f"Latencia: {resultado['avg_time_ms']} ms")
```

### Crear backup

```python
from backup_manager import BackupManager

manager = BackupManager("backups")
manager.create_backup("./proyecto", compression="zip")
```

### Limpiar disco

```python
from disk_cleaner import DiskCleaner

cleaner = DiskCleaner()
result = cleaner.scan_temp_folders()
print(f"Espacio a liberar: {cleaner._format_size(result['total_size'])}")
```

### Gestionar servicios

```python
from service_manager import ServiceManager

manager = ServiceManager()
services = manager.list_services(filter_running=True)
manager.restart_service("nombre_servicio")
```

### Auditoría de seguridad

```python
from security_checker import SecurityChecker

checker = SecurityChecker()
results = checker.run_full_audit()
print(checker.generate_report())
```

## Estructura del proyecto

```
sysadmin_toolkit/
├── main.py              # Menú principal (v3.0)
├── port_scanner.py      # Escáner de puertos TCP
├── log_parser.py        # Analizador de logs
├── system_monitor.py    # Monitor de recursos
├── network_utils.py     # Utilidades de red
├── backup_manager.py    # Gestor de backups
├── disk_cleaner.py      # Limpiador de disco
├── service_manager.py   # Gestor de servicios
├── security_checker.py  # Verificador de seguridad
├── requirements.txt     # Dependencias
└── README.md            # Documentación
```

## Dependencias

| Paquete | Versión | Uso |
|---------|---------|-----|
| psutil  | >=5.9.0 | Monitor de sistema, limpiador de disco |

## Notas

- Algunas funciones requieren permisos de administrador.
- El escaneo de puertos puede ser detectado por firewalls. Use solo en redes autorizadas.
- Los backups se almacenan por defecto en la carpeta `backups/`.
- La auditoría de seguridad proporciona una revisión básica, no reemplaza herramientas especializadas.

## Licencia

Uso libre para fines educativos y de administración de sistemas.
