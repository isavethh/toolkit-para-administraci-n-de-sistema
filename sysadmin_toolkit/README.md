# SysAdmin Toolkit

Conjunto de herramientas de línea de comandos para administración de sistemas, desarrollado en Python. Permite realizar tareas comunes de diagnóstico, monitoreo y mantenimiento de servidores y estaciones de trabajo.

<<<<<<< HEAD
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
- Permisos de administrador (para algunas funciones de monitoreo)
=======
## Características

### 1. Escáner de Puertos (`port_scanner.py`)
- Escaneo rápido de puertos comunes (22, 80, 443, etc.)
- Escaneo completo de rangos de puertos
- Detección automática de servicios
- Escaneo multi-hilo para mayor velocidad

### 2. Parser de Logs (`log_parser.py`)
- Soporte para múltiples formatos (syslog, Apache, nginx, Windows)
- Detección automática de formato
- Filtrado por nivel de severidad (ERROR, WARNING, INFO, etc.)
- Búsqueda por palabras clave y expresiones regulares
- Generación de reportes de errores
- Estadísticas y resúmenes

### 3. Monitor del Sistema (`system_monitor.py`)
- Monitoreo de CPU (uso, frecuencia, núcleos)
- Monitoreo de memoria RAM y swap
- Monitoreo de discos (uso, particiones, I/O)
- Monitoreo de red (tráfico, conexiones, interfaces)
- Lista de procesos con mayor consumo
- Dashboard en tiempo real
- Sistema de alertas configurables
>>>>>>> c045bfeaa28f12c49e6e67f097ddb51d678b37b7

## Instalación

```bash
cd sysadmin_toolkit
pip install -r requirements.txt
```

<<<<<<< HEAD
## Módulos

### 1. Escáner de Puertos (`port_scanner.py`)

Detecta puertos abiertos en un host local o remoto mediante conexiones TCP.

**Características:**
- Escaneo rápido de puertos comunes (22, 80, 443, etc.)
- Escaneo de rangos personalizados
- Ejecución multi-hilo para mayor velocidad
- Identificación automática de servicios

### 2. Parser de Logs (`log_parser.py`)

Analiza archivos de registro del sistema para extraer información relevante.

**Características:**
- Soporte para formatos: syslog, Apache, nginx, Windows Event
- Detección automática del formato
- Filtrado por nivel de severidad (ERROR, WARNING, INFO)
- Búsqueda por palabras clave y expresiones regulares
- Generación de reportes y estadísticas

### 3. Monitor del Sistema (`system_monitor.py`)

Muestra el estado actual de los recursos del equipo.

**Características:**
- Uso de CPU (porcentaje, núcleos, frecuencia)
- Memoria RAM y swap
- Espacio en disco por partición
- Tráfico de red y conexiones activas
- Lista de procesos ordenados por consumo
- Dashboard en tiempo real
- Alertas configurables por umbrales

### 4. Utilidades de Red (`network_utils.py`)

Herramientas para diagnóstico de conectividad de red.

**Características:**
- Ping a hosts con estadísticas
- Traceroute con tiempos por salto
- Búsqueda DNS directa e inversa
- Verificación de disponibilidad de múltiples hosts
- Detección de IP local y pública
- Comprobación de puertos específicos

### 5. Gestor de Backups (`backup_manager.py`)

Crea y administra copias de seguridad de archivos y directorios.

**Características:**
- Compresión en formato ZIP o TAR.GZ
- Exclusión de patrones (ej: `__pycache__`, `.git`)
- Restauración de backups
- Verificación de integridad mediante hash MD5
- Registro de backups en manifiesto JSON
- Estadísticas de espacio utilizado

## Uso

### Menú interactivo
=======
## Uso
>>>>>>> c045bfeaa28f12c49e6e67f097ddb51d678b37b7

```bash
python main.py
```

Esto abre un menú donde puedes seleccionar la herramienta que necesitas.

### Ejecución individual de módulos

```bash
python port_scanner.py
python log_parser.py
python system_monitor.py
python network_utils.py
python backup_manager.py
```

<<<<<<< HEAD
## Ejemplos
=======
## Dependencias
>>>>>>> c045bfeaa28f12c49e6e67f097ddb51d678b37b7

### Escanear puertos de un servidor

<<<<<<< HEAD
=======
🔧 Configuración

### Umbrales de alerta (system_monitor.py)
>>>>>>> c045bfeaa28f12c49e6e67f097ddb51d678b37b7
```python
from port_scanner import scan_ports, quick_scan

<<<<<<< HEAD
# Escaneo rápido (puertos comunes)
quick_scan("192.168.1.1")
=======
Ejemplos

### Escanear puertos de localhost:
```python
from port_scanner import quick_scan, scan_ports

# Escaneo rápido
quick_scan("localhost")
>>>>>>> c045bfeaa28f12c49e6e67f097ddb51d678b37b7

# Escaneo de rango específico
scan_ports("192.168.1.1", start_port=1, end_port=1000)
```

### Analizar un archivo de log

```python
from log_parser import LogParser

parser = LogParser()
parser.parse_file("/var/log/syslog")

# Obtener solo errores
errores = parser.filter_by_level("ERROR")

# Buscar por palabra clave
resultados = parser.filter_by_keyword("connection failed")

# Ver resumen
print(parser.get_summary())
```

### Monitorear recursos del sistema

```python
from system_monitor import SystemMonitor

monitor = SystemMonitor()

# Obtener uso de CPU
cpu = monitor.get_cpu_stats()
print(f"CPU: {cpu['percent_usage']}%")

# Obtener uso de memoria
mem = monitor.get_memory_stats()
print(f"RAM: {mem['ram']['percent_used']}%")

# Configurar umbral de alerta
monitor.set_threshold("cpu_percent", 90.0)
```

<<<<<<< HEAD
### Hacer ping a un host
=======
Notas
>>>>>>> c045bfeaa28f12c49e6e67f097ddb51d678b37b7

```python
from network_utils import NetworkUtils

<<<<<<< HEAD
utils = NetworkUtils()

# Ping simple
resultado = utils.ping("google.com", count=4)
print(f"Tiempo promedio: {resultado['avg_time_ms']} ms")

# Verificar múltiples hosts
hosts = ["google.com", "github.com", "192.168.1.1"]
resultados = utils.check_host_availability(hosts)
```

### Crear un backup

```python
from backup_manager import BackupManager

manager = BackupManager("mis_backups")

# Crear backup comprimido
resultado = manager.create_backup(
    source_path="./proyecto",
    backup_name="proyecto_v1",
    compression="zip"
)

# Listar backups existentes
backups = manager.list_backups()

# Restaurar un backup
manager.restore_backup(backup_id=1, restore_path="./restaurado")
```

## Estructura del proyecto

```
sysadmin_toolkit/
├── main.py              # Menú principal
├── port_scanner.py      # Escáner de puertos TCP
├── log_parser.py        # Analizador de logs
├── system_monitor.py    # Monitor de recursos
├── network_utils.py     # Utilidades de red
├── backup_manager.py    # Gestor de backups
├── requirements.txt     # Dependencias
└── README.md            # Documentación
```

## Dependencias

| Paquete | Versión | Descripción |
|---------|---------|-------------|
| psutil  | >=5.9.0 | Acceso a información del sistema (CPU, memoria, disco, red, procesos) |

## Notas

- Algunas funciones requieren permisos de administrador para acceder a información del sistema.
- El escaneo de puertos puede ser detectado por firewalls. Úselo solo en redes donde tenga autorización.
- Los backups se almacenan por defecto en la carpeta `backups/` del directorio actual.

## Licencia

Uso libre para fines educativos y de administración de sistemas.
=======
>>>>>>> c045bfeaa28f12c49e6e67f097ddb51d678b37b7
