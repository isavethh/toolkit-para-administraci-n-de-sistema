# 🔧 SysAdmin Toolkit

Un conjunto de herramientas de administración de sistemas escritas en Python.

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

## Instalación

```bash
# Clonar o descargar el proyecto
cd sysadmin_toolkit

# Instalar dependencias
pip install -r requirements.txt
```

## Uso

### Ejecutar el menú principal:
```bash
python main.py
```

### Ejecutar módulos individualmente:

```bash
# Escáner de puertos
python port_scanner.py

# Parser de logs
python log_parser.py

# Monitor del sistema
python system_monitor.py
```

## Dependencias

- **Python 3.7+**
- **psutil** - Para monitoreo del sistema

🔧 Configuración

### Umbrales de alerta (system_monitor.py)
```python
monitor = SystemMonitor()
monitor.set_threshold("cpu_percent", 80.0)      # Alerta si CPU > 80%
monitor.set_threshold("memory_percent", 85.0)   # Alerta si RAM > 85%
monitor.set_threshold("disk_percent", 90.0)     # Alerta si Disco > 90%
```

Ejemplos

### Escanear puertos de localhost:
```python
from port_scanner import quick_scan, scan_ports

# Escaneo rápido
quick_scan("localhost")

# Escaneo de rango específico
scan_ports("192.168.1.1", start_port=1, end_port=1000)
```

### Analizar un archivo de log:
```python
from log_parser import LogParser

parser = LogParser()
parser.parse_file("/var/log/syslog")

# Filtrar solo errores
errors = parser.filter_by_level("ERROR")

# Buscar palabra clave
results = parser.filter_by_keyword("failed")

# Ver resumen
print(parser.get_summary())
```

### Obtener información del sistema:
```python
from system_monitor import SystemMonitor

monitor = SystemMonitor()

# Información de CPU
cpu = monitor.get_cpu_stats()
print(f"Uso de CPU: {cpu['percent_usage']}%")

# Información de memoria
mem = monitor.get_memory_stats()
print(f"RAM usada: {mem['ram']['used_gb']} GB")

# Top procesos
processes = monitor.get_process_list(10, sort_by="memory")
```

Notas

- El escáner de puertos debe usarse solo en sistemas propios o con autorización
- Algunos módulos requieren permisos de administrador para acceder a cierta información
- El monitor del sistema puede consumir recursos si se ejecuta continuamente

