"""
Parser de Logs - Herramienta para analizar archivos de log del sistema
"""
import re
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Optional


class LogEntry:
    """Representa una entrada de log parseada."""
    def __init__(self, timestamp: str, level: str, source: str, message: str, raw: str):
        self.timestamp = timestamp
        self.level = level
        self.source = source
        self.message = message
        self.raw = raw
    
    def __repr__(self):
        return f"LogEntry({self.level}: {self.message[:50]}...)"


class LogParser:
    """Parser de logs con soporte para múltiples formatos."""
    
    # Patrones comunes de logs
    PATTERNS = {
        "syslog": r"^(\w{3}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2})\s+(\S+)\s+(\S+?)(?:\[\d+\])?:\s*(.*)$",
        "apache_access": r'^(\S+)\s+\S+\s+\S+\s+\[([^\]]+)\]\s+"([^"]+)"\s+(\d+)\s+(\d+)',
        "apache_error": r"^\[([^\]]+)\]\s+\[(\w+)\]\s+(?:\[pid\s+\d+\])?\s*(.*)$",
        "nginx": r'^(\S+)\s+-\s+-\s+\[([^\]]+)\]\s+"([^"]+)"\s+(\d+)\s+(\d+)',
        "windows_event": r"^(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})\s+(\w+)\s+(\S+)\s+(.*)$",
        "generic": r"^(\d{4}-\d{2}-\d{2}[\sT]\d{2}:\d{2}:\d{2}(?:\.\d+)?)\s*[-\s]*(\w+)?\s*[-\s]*(.*)$"
    }
    
    # Niveles de severidad
    SEVERITY_LEVELS = {
        "CRITICAL": 5, "FATAL": 5, "EMERGENCY": 5,
        "ERROR": 4, "ERR": 4,
        "WARNING": 3, "WARN": 3,
        "NOTICE": 2,
        "INFO": 1, "INFORMATION": 1,
        "DEBUG": 0, "TRACE": 0
    }
    
    def __init__(self, log_format: str = "auto"):
        self.log_format = log_format
        self.entries = []
        self.stats = defaultdict(int)
    
    def detect_format(self, line: str) -> Optional[str]:
        """Detecta automáticamente el formato del log."""
        for format_name, pattern in self.PATTERNS.items():
            if re.match(pattern, line):
                return format_name
        return "generic"
    
    def parse_line(self, line: str, format_type: str = None) -> Optional[LogEntry]:
        """Parsea una línea de log individual."""
        line = line.strip()
        if not line:
            return None
        
        format_type = format_type or self.log_format
        if format_type == "auto":
            format_type = self.detect_format(line)
        
        pattern = self.PATTERNS.get(format_type, self.PATTERNS["generic"])
        match = re.match(pattern, line)
        
        if match:
            groups = match.groups()
            if format_type in ["syslog"]:
                return LogEntry(groups[0], "INFO", groups[2], groups[3], line)
            elif format_type in ["apache_access", "nginx"]:
                status_code = groups[3] if len(groups) > 3 else "200"
                level = "ERROR" if status_code.startswith(("4", "5")) else "INFO"
                return LogEntry(groups[1], level, "web", groups[2], line)
            elif format_type == "apache_error":
                return LogEntry(groups[0], groups[1].upper(), "apache", groups[2], line)
            elif format_type in ["windows_event", "generic"]:
                level = groups[1].upper() if len(groups) > 1 and groups[1] else "INFO"
                message = groups[-1] if groups else line
                return LogEntry(groups[0], level, "system", message, line)
        
        # Fallback: retornar entrada genérica
        return LogEntry(datetime.now().isoformat(), "UNKNOWN", "unknown", line, line)
    
    def parse_file(self, filepath: str) -> list:
        """Parsea un archivo de log completo."""
        path = Path(filepath)
        if not path.exists():
            raise FileNotFoundError(f"Archivo no encontrado: {filepath}")
        
        self.entries = []
        self.stats = defaultdict(int)
        
        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
            for line_num, line in enumerate(f, 1):
                entry = self.parse_line(line)
                if entry:
                    self.entries.append(entry)
                    self.stats[entry.level] += 1
                    self.stats["total"] += 1
        
        return self.entries
    
    def filter_by_level(self, min_level: str) -> list:
        """Filtra entradas por nivel mínimo de severidad."""
        min_severity = self.SEVERITY_LEVELS.get(min_level.upper(), 0)
        return [
            entry for entry in self.entries
            if self.SEVERITY_LEVELS.get(entry.level, 0) >= min_severity
        ]
    
    def filter_by_keyword(self, keyword: str, case_sensitive: bool = False) -> list:
        """Filtra entradas que contengan una palabra clave."""
        if case_sensitive:
            return [e for e in self.entries if keyword in e.message]
        return [e for e in self.entries if keyword.lower() in e.message.lower()]
    
    def filter_by_regex(self, pattern: str) -> list:
        """Filtra entradas usando una expresión regular."""
        regex = re.compile(pattern, re.IGNORECASE)
        return [e for e in self.entries if regex.search(e.message)]
    
    def get_summary(self) -> dict:
        """Genera un resumen estadístico del log."""
        return {
            "total_entries": self.stats["total"],
            "by_level": {
                level: self.stats[level] 
                for level in ["CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG"]
                if self.stats[level] > 0
            },
            "unique_sources": len(set(e.source for e in self.entries)),
            "error_rate": (
                (self.stats["ERROR"] + self.stats["CRITICAL"]) / self.stats["total"] * 100
                if self.stats["total"] > 0 else 0
            )
        }
    
    def get_top_messages(self, n: int = 10) -> list:
        """Obtiene los mensajes más frecuentes."""
        message_counts = Counter(e.message for e in self.entries)
        return message_counts.most_common(n)
    
    def get_errors_report(self) -> str:
        """Genera un reporte de errores."""
        errors = self.filter_by_level("ERROR")
        
        report = []
        report.append("=" * 60)
        report.append("  REPORTE DE ERRORES")
        report.append("=" * 60)
        report.append(f"  Total de errores/críticos: {len(errors)}")
        report.append("")
        
        for entry in errors[:50]:  # Limitar a 50 entradas
            report.append(f"  [{entry.level}] {entry.timestamp}")
            report.append(f"    Fuente: {entry.source}")
            report.append(f"    Mensaje: {entry.message[:100]}")
            report.append("")
        
        if len(errors) > 50:
            report.append(f"  ... y {len(errors) - 50} errores más")
        
        report.append("=" * 60)
        return "\n".join(report)


def print_summary(parser: LogParser):
    """Imprime un resumen del análisis."""
    summary = parser.get_summary()
    
    print("\n" + "=" * 60)
    print("  RESUMEN DEL ANÁLISIS DE LOG")
    print("=" * 60)
    print(f"  Total de entradas: {summary['total_entries']}")
    print(f"  Fuentes únicas: {summary['unique_sources']}")
    print(f"  Tasa de errores: {summary['error_rate']:.2f}%")
    print("\n  Distribución por nivel:")
    
    for level, count in summary["by_level"].items():
        bar = "█" * min(int(count / max(summary["by_level"].values()) * 20), 20)
        print(f"    {level:10} {count:6} {bar}")
    
    print("\n  Top 5 mensajes más frecuentes:")
    for msg, count in parser.get_top_messages(5):
        print(f"    [{count:4}x] {msg[:50]}...")
    
    print("=" * 60 + "\n")


def create_sample_log():
    """Crea un archivo de log de ejemplo para pruebas."""
    sample_log = """2026-01-27 10:15:23 INFO server Sistema iniciado correctamente
2026-01-27 10:15:24 INFO auth Usuario admin conectado desde 192.168.1.100
2026-01-27 10:15:30 DEBUG database Conexión a base de datos establecida
2026-01-27 10:16:01 WARNING disk Uso de disco al 85%
2026-01-27 10:16:45 ERROR auth Intento de login fallido para usuario 'root'
2026-01-27 10:17:02 ERROR auth Intento de login fallido para usuario 'admin'
2026-01-27 10:17:15 CRITICAL security Múltiples intentos de login fallidos detectados
2026-01-27 10:18:00 INFO backup Backup automático iniciado
2026-01-27 10:18:30 INFO backup Backup completado: 150MB copiados
2026-01-27 10:19:00 WARNING memory Uso de memoria al 75%
2026-01-27 10:20:00 INFO server Heartbeat OK
2026-01-27 10:21:00 ERROR network Timeout en conexión a servidor externo
2026-01-27 10:22:00 INFO server Reconexión exitosa
2026-01-27 10:23:00 DEBUG cache Cache limpiado: 50MB liberados
2026-01-27 10:24:00 INFO cron Tarea programada ejecutada: cleanup.sh
"""
    
    filepath = Path("sample_system.log")
    filepath.write_text(sample_log)
    print(f"Archivo de ejemplo creado: {filepath.absolute()}")
    return str(filepath)


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("  Parser de Logs del Sistema")
    print("=" * 60)
    
    print("\nOpciones:")
    print("1. Analizar archivo de log existente")
    print("2. Crear y analizar log de ejemplo")
    
    opcion = input("\nSeleccione una opción (1-2): ").strip()
    
    if opcion == "1":
        filepath = input("Ingrese la ruta del archivo de log: ").strip()
    else:
        filepath = create_sample_log()
    
    try:
        parser = LogParser(log_format="auto")
        entries = parser.parse_file(filepath)
        
        print_summary(parser)
        
        # Opciones adicionales
        while True:
            print("\nAcciones disponibles:")
            print("1. Filtrar por palabra clave")
            print("2. Ver solo errores")
            print("3. Buscar con regex")
            print("4. Generar reporte de errores")
            print("5. Salir")
            
            accion = input("\nSeleccione una acción: ").strip()
            
            if accion == "1":
                keyword = input("Palabra clave: ").strip()
                results = parser.filter_by_keyword(keyword)
                print(f"\nEncontradas {len(results)} entradas con '{keyword}':")
                for e in results[:10]:
                    print(f"  [{e.level}] {e.message[:60]}")
            
            elif accion == "2":
                errors = parser.filter_by_level("ERROR")
                print(f"\nTotal de errores: {len(errors)}")
                for e in errors[:10]:
                    print(f"  [{e.level}] {e.timestamp} - {e.message[:50]}")
            
            elif accion == "3":
                pattern = input("Expresión regular: ").strip()
                results = parser.filter_by_regex(pattern)
                print(f"\nEncontradas {len(results)} coincidencias:")
                for e in results[:10]:
                    print(f"  [{e.level}] {e.message[:60]}")
            
            elif accion == "4":
                print(parser.get_errors_report())
            
            elif accion == "5":
                break
            
    except FileNotFoundError as e:
        print(f"\n[ERROR] {e}")
    except Exception as e:
        print(f"\n[ERROR] Error al procesar el archivo: {e}")
