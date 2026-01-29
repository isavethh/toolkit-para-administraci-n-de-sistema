"""
Limpiador de Disco - Herramienta para liberar espacio eliminando archivos temporales
"""
import os
import shutil
import platform
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Tuple


class DiskCleaner:
    """Limpiador de archivos temporales y basura del sistema."""
    
    def __init__(self):
        self.is_windows = platform.system().lower() == "windows"
        self.scan_results = []
        self.total_size = 0
        
        # Definir rutas de limpieza según el SO
        if self.is_windows:
            self.temp_paths = self._get_windows_temp_paths()
        else:
            self.temp_paths = self._get_linux_temp_paths()
        
        # Patrones de archivos a limpiar
        self.cleanup_patterns = [
            "*.tmp", "*.temp", "*.log", "*.bak", "*.old",
            "*.cache", "~*", "*.dmp", "Thumbs.db", ".DS_Store",
            "*.pyc", "__pycache__", "*.swp", "*.swo"
        ]
    
    def _get_windows_temp_paths(self) -> List[Dict]:
        """Obtiene rutas temporales en Windows."""
        user_home = Path.home()
        return [
            {"path": Path(os.environ.get("TEMP", "")), "name": "Temp Usuario", "safe": True},
            {"path": Path(os.environ.get("TMP", "")), "name": "TMP Usuario", "safe": True},
            {"path": Path("C:/Windows/Temp"), "name": "Temp Sistema", "safe": True},
            {"path": user_home / "AppData/Local/Temp", "name": "AppData Temp", "safe": True},
            {"path": user_home / "AppData/Local/Microsoft/Windows/INetCache", "name": "Cache Internet", "safe": True},
            {"path": user_home / "AppData/Local/Microsoft/Windows/Explorer", "name": "Cache Explorer", "safe": False},
            {"path": Path("C:/Windows/Prefetch"), "name": "Prefetch", "safe": False},
            {"path": user_home / "Downloads", "name": "Descargas (solo temp)", "safe": False},
        ]
    
    def _get_linux_temp_paths(self) -> List[Dict]:
        """Obtiene rutas temporales en Linux/Mac."""
        user_home = Path.home()
        return [
            {"path": Path("/tmp"), "name": "Temp Sistema", "safe": True},
            {"path": Path("/var/tmp"), "name": "Var Temp", "safe": True},
            {"path": user_home / ".cache", "name": "Cache Usuario", "safe": True},
            {"path": user_home / ".local/share/Trash", "name": "Papelera", "safe": True},
            {"path": Path("/var/log"), "name": "Logs (solo antiguos)", "safe": False},
        ]
    
    def _format_size(self, size_bytes: int) -> str:
        """Formatea el tamaño en bytes a formato legible."""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024
        return f"{size_bytes:.2f} PB"
    
    def _get_file_size(self, path: Path) -> int:
        """Obtiene el tamaño de un archivo o directorio."""
        try:
            if path.is_file():
                return path.stat().st_size
            elif path.is_dir():
                total = 0
                for entry in path.rglob('*'):
                    if entry.is_file():
                        try:
                            total += entry.stat().st_size
                        except (PermissionError, OSError):
                            pass
                return total
        except (PermissionError, OSError):
            pass
        return 0
    
    def _matches_pattern(self, filename: str) -> bool:
        """Verifica si un archivo coincide con los patrones de limpieza."""
        import fnmatch
        for pattern in self.cleanup_patterns:
            if fnmatch.fnmatch(filename.lower(), pattern.lower()):
                return True
        return False
    
    def scan_temp_folders(self, include_unsafe: bool = False) -> Dict:
        """
        Escanea carpetas temporales para encontrar archivos a limpiar.
        
        Args:
            include_unsafe: Incluir carpetas marcadas como no seguras
        
        Returns:
            Diccionario con resultados del escaneo
        """
        self.scan_results = []
        self.total_size = 0
        
        results = {
            "folders": [],
            "total_files": 0,
            "total_size": 0,
            "errors": []
        }
        
        for temp_info in self.temp_paths:
            if not include_unsafe and not temp_info.get("safe", True):
                continue
            
            path = temp_info["path"]
            if not path.exists():
                continue
            
            folder_result = {
                "name": temp_info["name"],
                "path": str(path),
                "files": [],
                "file_count": 0,
                "size": 0
            }
            
            try:
                for entry in path.rglob('*'):
                    if entry.is_file():
                        try:
                            size = entry.stat().st_size
                            folder_result["files"].append({
                                "path": str(entry),
                                "name": entry.name,
                                "size": size
                            })
                            folder_result["file_count"] += 1
                            folder_result["size"] += size
                        except (PermissionError, OSError):
                            pass
            except (PermissionError, OSError) as e:
                results["errors"].append(f"{temp_info['name']}: {str(e)}")
            
            if folder_result["file_count"] > 0:
                results["folders"].append(folder_result)
                results["total_files"] += folder_result["file_count"]
                results["total_size"] += folder_result["size"]
        
        self.scan_results = results["folders"]
        self.total_size = results["total_size"]
        
        return results
    
    def scan_old_files(self, directory: str, days_old: int = 30) -> Dict:
        """
        Busca archivos más antiguos que cierta cantidad de días.
        
        Args:
            directory: Directorio a escanear
            days_old: Antigüedad mínima en días
        
        Returns:
            Diccionario con archivos encontrados
        """
        path = Path(directory)
        if not path.exists():
            return {"error": f"Directorio no encontrado: {directory}"}
        
        cutoff_date = datetime.now() - timedelta(days=days_old)
        old_files = []
        total_size = 0
        
        try:
            for entry in path.rglob('*'):
                if entry.is_file():
                    try:
                        mtime = datetime.fromtimestamp(entry.stat().st_mtime)
                        if mtime < cutoff_date:
                            size = entry.stat().st_size
                            old_files.append({
                                "path": str(entry),
                                "name": entry.name,
                                "size": size,
                                "modified": mtime.strftime("%Y-%m-%d"),
                                "age_days": (datetime.now() - mtime).days
                            })
                            total_size += size
                    except (PermissionError, OSError):
                        pass
        except (PermissionError, OSError) as e:
            return {"error": str(e)}
        
        return {
            "directory": directory,
            "days_threshold": days_old,
            "files": old_files,
            "file_count": len(old_files),
            "total_size": total_size,
            "total_size_formatted": self._format_size(total_size)
        }
    
    def scan_large_files(self, directory: str, min_size_mb: int = 100) -> Dict:
        """
        Busca archivos grandes en un directorio.
        
        Args:
            directory: Directorio a escanear
            min_size_mb: Tamaño mínimo en MB
        
        Returns:
            Diccionario con archivos encontrados
        """
        path = Path(directory)
        if not path.exists():
            return {"error": f"Directorio no encontrado: {directory}"}
        
        min_size_bytes = min_size_mb * 1024 * 1024
        large_files = []
        total_size = 0
        
        try:
            for entry in path.rglob('*'):
                if entry.is_file():
                    try:
                        size = entry.stat().st_size
                        if size >= min_size_bytes:
                            large_files.append({
                                "path": str(entry),
                                "name": entry.name,
                                "size": size,
                                "size_formatted": self._format_size(size)
                            })
                            total_size += size
                    except (PermissionError, OSError):
                        pass
        except (PermissionError, OSError) as e:
            return {"error": str(e)}
        
        # Ordenar por tamaño descendente
        large_files.sort(key=lambda x: x["size"], reverse=True)
        
        return {
            "directory": directory,
            "min_size_mb": min_size_mb,
            "files": large_files,
            "file_count": len(large_files),
            "total_size": total_size,
            "total_size_formatted": self._format_size(total_size)
        }
    
    def scan_duplicates(self, directory: str) -> Dict:
        """
        Busca archivos duplicados basándose en tamaño y nombre.
        
        Args:
            directory: Directorio a escanear
        
        Returns:
            Diccionario con duplicados encontrados
        """
        import hashlib
        
        path = Path(directory)
        if not path.exists():
            return {"error": f"Directorio no encontrado: {directory}"}
        
        # Agrupar por tamaño primero (más eficiente)
        size_groups = {}
        
        try:
            for entry in path.rglob('*'):
                if entry.is_file():
                    try:
                        size = entry.stat().st_size
                        if size > 0:  # Ignorar archivos vacíos
                            if size not in size_groups:
                                size_groups[size] = []
                            size_groups[size].append(entry)
                    except (PermissionError, OSError):
                        pass
        except (PermissionError, OSError) as e:
            return {"error": str(e)}
        
        # Calcular hash para archivos con mismo tamaño
        duplicates = []
        wasted_space = 0
        
        for size, files in size_groups.items():
            if len(files) < 2:
                continue
            
            # Calcular hash parcial (primeros 1KB)
            hash_groups = {}
            for file_path in files:
                try:
                    with open(file_path, 'rb') as f:
                        file_hash = hashlib.md5(f.read(1024)).hexdigest()
                    
                    if file_hash not in hash_groups:
                        hash_groups[file_hash] = []
                    hash_groups[file_hash].append(file_path)
                except (PermissionError, OSError):
                    pass
            
            for file_hash, dup_files in hash_groups.items():
                if len(dup_files) > 1:
                    duplicates.append({
                        "files": [str(f) for f in dup_files],
                        "count": len(dup_files),
                        "size_each": size,
                        "size_each_formatted": self._format_size(size),
                        "wasted": size * (len(dup_files) - 1)
                    })
                    wasted_space += size * (len(dup_files) - 1)
        
        return {
            "directory": directory,
            "duplicate_groups": duplicates,
            "total_groups": len(duplicates),
            "wasted_space": wasted_space,
            "wasted_space_formatted": self._format_size(wasted_space)
        }
    
    def clean_temp_folders(self, dry_run: bool = True) -> Dict:
        """
        Limpia las carpetas temporales escaneadas.
        
        Args:
            dry_run: Si es True, solo simula la limpieza
        
        Returns:
            Diccionario con resultados de la limpieza
        """
        if not self.scan_results:
            return {"error": "Ejecute scan_temp_folders primero"}
        
        results = {
            "deleted_files": 0,
            "deleted_size": 0,
            "errors": [],
            "dry_run": dry_run
        }
        
        for folder in self.scan_results:
            for file_info in folder["files"]:
                file_path = Path(file_info["path"])
                
                try:
                    if not dry_run:
                        if file_path.is_file():
                            file_path.unlink()
                        elif file_path.is_dir():
                            shutil.rmtree(file_path)
                    
                    results["deleted_files"] += 1
                    results["deleted_size"] += file_info["size"]
                except (PermissionError, OSError) as e:
                    results["errors"].append(f"{file_info['name']}: {str(e)}")
        
        results["deleted_size_formatted"] = self._format_size(results["deleted_size"])
        return results
    
    def delete_files(self, file_paths: List[str], dry_run: bool = True) -> Dict:
        """
        Elimina una lista específica de archivos.
        
        Args:
            file_paths: Lista de rutas de archivos a eliminar
            dry_run: Si es True, solo simula la eliminación
        
        Returns:
            Diccionario con resultados
        """
        results = {
            "deleted": [],
            "errors": [],
            "total_size": 0,
            "dry_run": dry_run
        }
        
        for file_path in file_paths:
            path = Path(file_path)
            
            try:
                if path.exists():
                    size = self._get_file_size(path)
                    
                    if not dry_run:
                        if path.is_file():
                            path.unlink()
                        elif path.is_dir():
                            shutil.rmtree(path)
                    
                    results["deleted"].append({"path": file_path, "size": size})
                    results["total_size"] += size
                else:
                    results["errors"].append(f"No encontrado: {file_path}")
            except (PermissionError, OSError) as e:
                results["errors"].append(f"{file_path}: {str(e)}")
        
        results["total_size_formatted"] = self._format_size(results["total_size"])
        return results
    
    def empty_recycle_bin(self) -> Dict:
        """Vacía la papelera de reciclaje (solo Windows)."""
        if not self.is_windows:
            # En Linux, limpiar ~/.local/share/Trash
            trash_path = Path.home() / ".local/share/Trash"
            if trash_path.exists():
                try:
                    for folder in ["files", "info"]:
                        folder_path = trash_path / folder
                        if folder_path.exists():
                            for item in folder_path.iterdir():
                                try:
                                    if item.is_file():
                                        item.unlink()
                                    else:
                                        shutil.rmtree(item)
                                except (PermissionError, OSError):
                                    pass
                    return {"success": True, "message": "Papelera vaciada"}
                except Exception as e:
                    return {"success": False, "error": str(e)}
            return {"success": False, "error": "Papelera no encontrada"}
        
        try:
            import ctypes
            # SHEmptyRecycleBin
            SHERB_NOCONFIRMATION = 0x00000001
            SHERB_NOPROGRESSUI = 0x00000002
            SHERB_NOSOUND = 0x00000004
            
            ctypes.windll.shell32.SHEmptyRecycleBinW(
                None, None, 
                SHERB_NOCONFIRMATION | SHERB_NOPROGRESSUI | SHERB_NOSOUND
            )
            return {"success": True, "message": "Papelera vaciada"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_disk_usage(self) -> List[Dict]:
        """Obtiene el uso de disco de todas las particiones."""
        try:
            import psutil
            
            partitions = []
            for partition in psutil.disk_partitions():
                try:
                    usage = psutil.disk_usage(partition.mountpoint)
                    partitions.append({
                        "device": partition.device,
                        "mountpoint": partition.mountpoint,
                        "fstype": partition.fstype,
                        "total": self._format_size(usage.total),
                        "used": self._format_size(usage.used),
                        "free": self._format_size(usage.free),
                        "percent": usage.percent
                    })
                except (PermissionError, OSError):
                    pass
            
            return partitions
        except ImportError:
            return [{"error": "psutil no instalado"}]


def run_disk_cleaner():
    """Ejecuta el limpiador de disco interactivo."""
    cleaner = DiskCleaner()
    
    while True:
        print("\n" + "="*60)
        print("  LIMPIADOR DE DISCO")
        print("="*60)
        print("\n  Opciones:")
        print("  1. Escanear carpetas temporales")
        print("  2. Buscar archivos antiguos")
        print("  3. Buscar archivos grandes")
        print("  4. Buscar archivos duplicados")
        print("  5. Ver uso de disco")
        print("  6. Vaciar papelera")
        print("  7. Volver")
        
        opcion = input("\n  Seleccione (1-7): ").strip()
        
        if opcion == "1":
            include_unsafe = input("  ¿Incluir carpetas no seguras? (s/n): ").strip().lower() == 's'
            
            print("\n  Escaneando...")
            result = cleaner.scan_temp_folders(include_unsafe)
            
            print(f"\n  Archivos encontrados: {result['total_files']}")
            print(f"  Espacio a liberar: {cleaner._format_size(result['total_size'])}")
            
            if result['folders']:
                print(f"\n  {'CARPETA':<30} {'ARCHIVOS':>10} {'TAMAÑO':>15}")
                print("  " + "-"*60)
                for folder in result['folders']:
                    print(f"  {folder['name'][:30]:<30} {folder['file_count']:>10} {cleaner._format_size(folder['size']):>15}")
            
            if result['total_files'] > 0:
                limpiar = input("\n  ¿Limpiar archivos? (s/n): ").strip().lower()
                if limpiar == 's':
                    confirm = input("  ¿Confirmar eliminación? (s/n): ").strip().lower()
                    if confirm == 's':
                        clean_result = cleaner.clean_temp_folders(dry_run=False)
                        print(f"\n  ✓ Eliminados: {clean_result['deleted_files']} archivos")
                        print(f"  ✓ Liberado: {clean_result['deleted_size_formatted']}")
                        if clean_result['errors']:
                            print(f"  ⚠ Errores: {len(clean_result['errors'])}")
        
        elif opcion == "2":
            directory = input("  Directorio a escanear: ").strip()
            days = input("  Antigüedad mínima en días (30): ").strip()
            days = int(days) if days.isdigit() else 30
            
            print("\n  Buscando archivos antiguos...")
            result = cleaner.scan_old_files(directory, days)
            
            if "error" in result:
                print(f"\n  Error: {result['error']}")
            else:
                print(f"\n  Archivos mayores a {days} días: {result['file_count']}")
                print(f"  Espacio ocupado: {result['total_size_formatted']}")
                
                if result['files']:
                    print(f"\n  {'ARCHIVO':<40} {'TAMAÑO':>12} {'EDAD'}")
                    print("  " + "-"*65)
                    for f in result['files'][:15]:
                        print(f"  {f['name'][:40]:<40} {cleaner._format_size(f['size']):>12} {f['age_days']} días")
                    if len(result['files']) > 15:
                        print(f"  ... y {len(result['files']) - 15} archivos más")
        
        elif opcion == "3":
            directory = input("  Directorio a escanear: ").strip()
            min_size = input("  Tamaño mínimo en MB (100): ").strip()
            min_size = int(min_size) if min_size.isdigit() else 100
            
            print("\n  Buscando archivos grandes...")
            result = cleaner.scan_large_files(directory, min_size)
            
            if "error" in result:
                print(f"\n  Error: {result['error']}")
            else:
                print(f"\n  Archivos mayores a {min_size} MB: {result['file_count']}")
                print(f"  Espacio total: {result['total_size_formatted']}")
                
                if result['files']:
                    print(f"\n  {'ARCHIVO':<50} {'TAMAÑO':>15}")
                    print("  " + "-"*70)
                    for f in result['files'][:20]:
                        print(f"  {f['name'][:50]:<50} {f['size_formatted']:>15}")
        
        elif opcion == "4":
            directory = input("  Directorio a escanear: ").strip()
            
            print("\n  Buscando duplicados (puede tardar)...")
            result = cleaner.scan_duplicates(directory)
            
            if "error" in result:
                print(f"\n  Error: {result['error']}")
            else:
                print(f"\n  Grupos de duplicados: {result['total_groups']}")
                print(f"  Espacio desperdiciado: {result['wasted_space_formatted']}")
                
                if result['duplicate_groups']:
                    for i, group in enumerate(result['duplicate_groups'][:5], 1):
                        print(f"\n  Grupo {i} ({group['count']} archivos, {group['size_each_formatted']} c/u):")
                        for f in group['files'][:3]:
                            print(f"    - {f}")
        
        elif opcion == "5":
            partitions = cleaner.get_disk_usage()
            
            print(f"\n  {'DISCO':<15} {'SISTEMA':>10} {'TOTAL':>12} {'USADO':>12} {'LIBRE':>12} {'%'}")
            print("  " + "-"*75)
            for p in partitions:
                if "error" not in p:
                    print(f"  {p['mountpoint']:<15} {p['fstype']:>10} {p['total']:>12} {p['used']:>12} {p['free']:>12} {p['percent']:>5.1f}%")
        
        elif opcion == "6":
            confirm = input("  ¿Vaciar papelera? (s/n): ").strip().lower()
            if confirm == 's':
                result = cleaner.empty_recycle_bin()
                if result['success']:
                    print(f"\n  ✓ {result['message']}")
                else:
                    print(f"\n  ✗ Error: {result.get('error')}")
        
        elif opcion == "7":
            break


if __name__ == "__main__":
    run_disk_cleaner()
