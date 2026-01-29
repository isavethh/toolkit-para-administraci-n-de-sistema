"""
SysAdmin Toolkit - Herramientas de administración de sistemas en Python

Este toolkit incluye:
- Escáner de puertos
- Parser de logs
- Monitor del sistema
- Utilidades de red
- Gestor de backups

Autor: SysAdmin Toolkit
Versión: 2.0
Fecha: Enero 2026
"""
import sys


def show_banner():
    """Muestra el banner del programa."""
    banner = """
╔══════════════════════════════════════════════════════════════════╗
║                                                                  ║
║   ███████╗██╗   ██╗███████╗ █████╗ ██████╗ ███╗   ███╗██╗███╗   ██║
║   ██╔════╝╚██╗ ██╔╝██╔════╝██╔══██╗██╔══██╗████╗ ████║██║████╗  ██║
║   ███████╗ ╚████╔╝ ███████╗███████║██║  ██║██╔████╔██║██║██╔██╗ ██║
║   ╚════██║  ╚██╔╝  ╚════██║██╔══██║██║  ██║██║╚██╔╝██║██║██║╚██╗██║
║   ███████║   ██║   ███████║██║  ██║██████╔╝██║ ╚═╝ ██║██║██║ ╚████║
║   ╚══════╝   ╚═╝   ╚══════╝╚═╝  ╚═╝╚═════╝ ╚═╝     ╚═╝╚═╝╚═╝  ╚═══║
║                                                                  ║
║                    🔧 TOOLKIT v2.0                               ║
║         Herramientas de Administración de Sistemas               ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
    """
    print(banner)


def show_menu():
    """Muestra el menú principal."""
    print("""
┌──────────────────────────────────────────────────────────────────┐
│                      MENÚ PRINCIPAL                              │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│   [1] 🔍 Escáner de Puertos                                      │
│       Escanea puertos abiertos en un host                        │
│                                                                  │
│   [2] 📋 Parser de Logs                                          │
│       Analiza y filtra archivos de log                           │
│                                                                  │
│   [3] 📊 Monitor del Sistema                                     │
│       Monitorea CPU, memoria, disco y red                        │
│                                                                  │
│   [4] 🌐 Utilidades de Red                                       │
│       Ping, traceroute, DNS y diagnósticos                       │
│                                                                  │
│   [5] 💾 Gestor de Backups                                       │
│       Crea y gestiona copias de seguridad                        │
│                                                                  │
│   [6] ❌ Salir                                                    │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
    """)


def run_port_scanner():
    """Ejecuta el escáner de puertos."""
    print("\n" + "="*60)
    print("  ESCÁNER DE PUERTOS")
    print("="*60)
    
    from port_scanner import scan_ports, quick_scan
    
    target = input("\n  Ingrese el host a escanear (ej: localhost): ").strip()
    if not target:
        target = "localhost"
    
    print("\n  Opciones de escaneo:")
    print("  1. Escaneo rápido (puertos comunes)")
    print("  2. Escaneo completo (1-1024)")
    print("  3. Rango personalizado")
    
    opcion = input("\n  Seleccione (1-3): ").strip()
    
    if opcion == "1":
        quick_scan(target)
    elif opcion == "2":
        scan_ports(target, 1, 1024)
    elif opcion == "3":
        try:
            start = int(input("  Puerto inicial: "))
            end = int(input("  Puerto final: "))
            scan_ports(target, start, end)
        except ValueError:
            print("  [ERROR] Ingrese números válidos")
    else:
        print("  Opción no válida")


def run_log_parser():
    """Ejecuta el parser de logs."""
    print("\n" + "="*60)
    print("  PARSER DE LOGS")
    print("="*60)
    
    from log_parser import LogParser, print_summary, create_sample_log
    
    print("\n  Opciones:")
    print("  1. Analizar archivo de log existente")
    print("  2. Crear y analizar log de ejemplo")
    
    opcion = input("\n  Seleccione (1-2): ").strip()
    
    if opcion == "1":
        filepath = input("  Ruta del archivo de log: ").strip()
    else:
        filepath = create_sample_log()
    
    try:
        parser = LogParser(log_format="auto")
        parser.parse_file(filepath)
        print_summary(parser)
        
        while True:
            print("\n  Acciones:")
            print("  1. Filtrar por palabra clave")
            print("  2. Ver solo errores")
            print("  3. Generar reporte de errores")
            print("  4. Volver al menú principal")
            
            accion = input("\n  Seleccione: ").strip()
            
            if accion == "1":
                keyword = input("  Palabra clave: ").strip()
                results = parser.filter_by_keyword(keyword)
                print(f"\n  Encontradas {len(results)} entradas:")
                for e in results[:10]:
                    print(f"    [{e.level}] {e.message[:60]}")
            elif accion == "2":
                errors = parser.filter_by_level("ERROR")
                print(f"\n  Total de errores: {len(errors)}")
                for e in errors[:10]:
                    print(f"    [{e.level}] {e.message[:50]}")
            elif accion == "3":
                print(parser.get_errors_report())
            elif accion == "4":
                break
                
    except FileNotFoundError as e:
        print(f"\n  [ERROR] {e}")
    except Exception as e:
        print(f"\n  [ERROR] {e}")


def run_system_monitor():
    """Ejecuta el monitor del sistema."""
    print("\n" + "="*60)
    print("  MONITOR DEL SISTEMA")
    print("="*60)
    
    try:
        from system_monitor import SystemMonitor, display_dashboard, print_single_report
    except ImportError as e:
        print(f"\n  [ERROR] {e}")
        print("  Instale psutil: pip install psutil")
        return
    
    monitor = SystemMonitor()
    
    print("\n  Opciones:")
    print("  1. Dashboard en tiempo real")
    print("  2. Reporte único del sistema")
    print("  3. Ver top procesos")
    
    opcion = input("\n  Seleccione (1-3): ").strip()
    
    if opcion == "1":
        print("\n  Iniciando dashboard... (Ctrl+C para salir)")
        display_dashboard(monitor)
    elif opcion == "2":
        print_single_report(monitor)
    elif opcion == "3":
        processes = monitor.get_process_list(15, "memory")
        print(f"\n  {'PID':>7}  {'NOMBRE':<30}  {'CPU%':>6}  {'MEM%':>6}")
        print("  " + "-" * 55)
        for proc in processes:
            print(f"  {proc['pid']:>7}  {proc['name'][:30]:<30}  {proc['cpu_percent']:>5.1f}%  {proc['memory_percent']:>5.1f}%")
    else:
        print("  Opción no válida")


def run_network_utils():
    """Ejecuta las utilidades de red."""
    print("\n" + "="*60)
    print("  UTILIDADES DE RED")
    print("="*60)
    
    try:
        from network_utils import run_network_diagnostic
        run_network_diagnostic()
    except ImportError as e:
        print(f"\n  [ERROR] No se pudo cargar el módulo: {e}")


def run_backup_manager():
    """Ejecuta el gestor de backups."""
    print("\n" + "="*60)
    print("  GESTOR DE BACKUPS")
    print("="*60)
    
    try:
        from backup_manager import run_backup_manager as run_backup
        run_backup()
    except ImportError as e:
        print(f"\n  [ERROR] No se pudo cargar el módulo: {e}")


def main():
    """Función principal del programa."""
    show_banner()
    
    while True:
        show_menu()
        opcion = input("  Seleccione una opción (1-6): ").strip()
        
        if opcion == "1":
            run_port_scanner()
        elif opcion == "2":
            run_log_parser()
        elif opcion == "3":
            run_system_monitor()
        elif opcion == "4":
            run_network_utils()
        elif opcion == "5":
            run_backup_manager()
        elif opcion == "6":
            print("\n  ¡Hasta luego! 👋\n")
            sys.exit(0)
        else:
            print("\n  [!] Opción no válida. Intente de nuevo.")
        
        input("\n  Presione Enter para continuar...")


if __name__ == "__main__":
    main()
