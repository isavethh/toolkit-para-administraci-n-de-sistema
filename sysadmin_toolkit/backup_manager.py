"""
Gestor de Backups - Herramienta para crear y gestionar copias de seguridad
"""
import os
import shutil
import hashlib
import json
import zipfile
import tarfile
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional


class BackupManager:
    """Gestor de copias de seguridad."""
    
    def __init__(self, backup_dir: str = "backups"):
        """
        Inicializa el gestor de backups.
        
        Args:
            backup_dir: Directorio donde se almacenarán los backups
        """
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self.manifest_file = self.backup_dir / "backup_manifest.json"
        self.manifest = self._load_manifest()
    
    def _load_manifest(self) -> Dict:
        """Carga el manifiesto de backups."""
        if self.manifest_file.exists():
            try:
                with open(self.manifest_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                pass
        return {"backups": [], "version": "1.0"}
    
    def _save_manifest(self):
        """Guarda el manifiesto de backups."""
        with open(self.manifest_file, 'w', encoding='utf-8') as f:
            json.dump(self.manifest, f, indent=2, ensure_ascii=False)
    
    def _calculate_hash(self, filepath: Path) -> str:
        """Calcula el hash MD5 de un archivo."""
        hash_md5 = hashlib.md5()
        try:
            with open(filepath, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except Exception:
            return ""
    
    def _get_dir_size(self, path: Path) -> int:
        """Calcula el tamaño total de un directorio."""
        total = 0
        try:
            for entry in path.rglob('*'):
                if entry.is_file():
                    total += entry.stat().st_size
        except Exception:
            pass
        return total
    
    def _format_size(self, size_bytes: int) -> str:
        """Formatea el tamaño en bytes a formato legible."""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024
        return f"{size_bytes:.2f} PB"
    
    def create_backup(
        self, 
        source_path: str, 
        backup_name: Optional[str] = None,
        compression: str = "zip",
        exclude_patterns: List[str] = None
    ) -> Dict:
        """
        Crea un backup de un archivo o directorio.
        
        Args:
            source_path: Ruta del archivo o directorio a respaldar
            backup_name: Nombre del backup (opcional)
            compression: Tipo de compresión ('zip', 'tar.gz', 'none')
            exclude_patterns: Patrones a excluir (ej: ['*.tmp', '__pycache__'])
        
        Returns:
            Diccionario con información del backup creado
        """
        source = Path(source_path)
        
        if not source.exists():
            return {"success": False, "error": f"Ruta no encontrada: {source_path}"}
        
        exclude_patterns = exclude_patterns or ['__pycache__', '*.pyc', '.git', 'node_modules']
        
        # Generar nombre del backup
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_name = backup_name or source.name
        
        # Determinar extensión según compresión
        if compression == "zip":
            ext = ".zip"
        elif compression == "tar.gz":
            ext = ".tar.gz"
        else:
            ext = ""
        
        backup_filename = f"{base_name}_{timestamp}{ext}"
        backup_path = self.backup_dir / backup_filename
        
        try:
            start_time = datetime.now()
            files_count = 0
            total_size = 0
            
            if compression == "zip":
                with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    if source.is_file():
                        zipf.write(source, source.name)
                        files_count = 1
                        total_size = source.stat().st_size
                    else:
                        for file_path in source.rglob('*'):
                            # Verificar exclusiones
                            if self._should_exclude(file_path, exclude_patterns):
                                continue
                            
                            if file_path.is_file():
                                arcname = file_path.relative_to(source)
                                zipf.write(file_path, arcname)
                                files_count += 1
                                total_size += file_path.stat().st_size
            
            elif compression == "tar.gz":
                with tarfile.open(backup_path, "w:gz") as tar:
                    def filter_func(tarinfo):
                        if self._should_exclude(Path(tarinfo.name), exclude_patterns):
                            return None
                        return tarinfo
                    
                    tar.add(source, arcname=source.name, filter=filter_func)
                    files_count = sum(1 for _ in source.rglob('*') if _.is_file())
                    total_size = self._get_dir_size(source)
            
            else:
                # Sin compresión - copiar directorio
                if source.is_file():
                    backup_path = self.backup_dir / backup_filename
                    shutil.copy2(source, backup_path)
                    files_count = 1
                    total_size = source.stat().st_size
                else:
                    shutil.copytree(source, backup_path, 
                                   ignore=shutil.ignore_patterns(*exclude_patterns))
                    files_count = sum(1 for _ in backup_path.rglob('*') if _.is_file())
                    total_size = self._get_dir_size(backup_path)
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            # Calcular tamaño del backup
            backup_size = backup_path.stat().st_size if backup_path.is_file() else self._get_dir_size(backup_path)
            
            # Registrar en manifiesto
            backup_info = {
                "id": len(self.manifest["backups"]) + 1,
                "name": backup_filename,
                "source": str(source.absolute()),
                "path": str(backup_path.absolute()),
                "created": timestamp,
                "compression": compression,
                "files_count": files_count,
                "original_size": total_size,
                "backup_size": backup_size,
                "duration_seconds": round(duration, 2),
                "hash": self._calculate_hash(backup_path) if backup_path.is_file() else ""
            }
            
            self.manifest["backups"].append(backup_info)
            self._save_manifest()
            
            return {
                "success": True,
                "backup_path": str(backup_path),
                "files_count": files_count,
                "original_size": self._format_size(total_size),
                "backup_size": self._format_size(backup_size),
                "compression_ratio": f"{(1 - backup_size/total_size)*100:.1f}%" if total_size > 0 else "0%",
                "duration": f"{duration:.2f}s"
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _should_exclude(self, path: Path, patterns: List[str]) -> bool:
        """Verifica si un archivo debe ser excluido."""
        path_str = str(path)
        for pattern in patterns:
            if pattern.startswith('*'):
                if path_str.endswith(pattern[1:]):
                    return True
            elif pattern in path_str:
                return True
        return False
    
    def restore_backup(self, backup_id: int, restore_path: str = None) -> Dict:
        """
        Restaura un backup existente.
        
        Args:
            backup_id: ID del backup a restaurar
            restore_path: Ruta donde restaurar (opcional, usa ruta original si no se especifica)
        
        Returns:
            Diccionario con resultado de la restauración
        """
        # Buscar backup en manifiesto
        backup_info = None
        for backup in self.manifest["backups"]:
            if backup["id"] == backup_id:
                backup_info = backup
                break
        
        if not backup_info:
            return {"success": False, "error": f"Backup con ID {backup_id} no encontrado"}
        
        backup_path = Path(backup_info["path"])
        if not backup_path.exists():
            return {"success": False, "error": f"Archivo de backup no encontrado: {backup_path}"}
        
        # Determinar ruta de restauración
        if restore_path:
            dest = Path(restore_path)
        else:
            dest = Path(backup_info["source"]).parent / f"restored_{backup_info['name']}"
        
        try:
            compression = backup_info.get("compression", "zip")
            
            if compression == "zip":
                with zipfile.ZipFile(backup_path, 'r') as zipf:
                    zipf.extractall(dest)
            
            elif compression == "tar.gz":
                with tarfile.open(backup_path, "r:gz") as tar:
                    tar.extractall(dest)
            
            else:
                if backup_path.is_file():
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(backup_path, dest)
                else:
                    shutil.copytree(backup_path, dest)
            
            return {
                "success": True,
                "restored_to": str(dest.absolute()),
                "backup_name": backup_info["name"]
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def list_backups(self) -> List[Dict]:
        """Lista todos los backups disponibles."""
        backups = []
        for backup in self.manifest["backups"]:
            path = Path(backup["path"])
            exists = path.exists()
            backups.append({
                "id": backup["id"],
                "name": backup["name"],
                "created": backup["created"],
                "size": self._format_size(backup.get("backup_size", 0)),
                "files": backup.get("files_count", 0),
                "exists": exists
            })
        return backups
    
    def delete_backup(self, backup_id: int) -> Dict:
        """
        Elimina un backup.
        
        Args:
            backup_id: ID del backup a eliminar
        
        Returns:
            Diccionario con resultado
        """
        for i, backup in enumerate(self.manifest["backups"]):
            if backup["id"] == backup_id:
                backup_path = Path(backup["path"])
                
                try:
                    if backup_path.exists():
                        if backup_path.is_file():
                            backup_path.unlink()
                        else:
                            shutil.rmtree(backup_path)
                    
                    del self.manifest["backups"][i]
                    self._save_manifest()
                    
                    return {"success": True, "message": f"Backup {backup_id} eliminado"}
                except Exception as e:
                    return {"success": False, "error": str(e)}
        
        return {"success": False, "error": f"Backup {backup_id} no encontrado"}
    
    def verify_backup(self, backup_id: int) -> Dict:
        """
        Verifica la integridad de un backup.
        
        Args:
            backup_id: ID del backup a verificar
        
        Returns:
            Diccionario con resultado de la verificación
        """
        for backup in self.manifest["backups"]:
            if backup["id"] == backup_id:
                backup_path = Path(backup["path"])
                
                if not backup_path.exists():
                    return {"success": False, "valid": False, "error": "Archivo no encontrado"}
                
                if not backup_path.is_file():
                    return {"success": True, "valid": True, "message": "Directorio existe"}
                
                # Verificar hash
                current_hash = self._calculate_hash(backup_path)
                original_hash = backup.get("hash", "")
                
                if original_hash and current_hash == original_hash:
                    return {
                        "success": True, 
                        "valid": True, 
                        "message": "Backup verificado correctamente",
                        "hash": current_hash
                    }
                elif not original_hash:
                    return {
                        "success": True,
                        "valid": True,
                        "message": "Archivo existe (sin hash para verificar)"
                    }
                else:
                    return {
                        "success": True,
                        "valid": False,
                        "message": "Hash no coincide - archivo posiblemente corrupto",
                        "expected": original_hash,
                        "actual": current_hash
                    }
        
        return {"success": False, "error": f"Backup {backup_id} no encontrado"}
    
    def get_backup_stats(self) -> Dict:
        """Obtiene estadísticas de los backups."""
        total_backups = len(self.manifest["backups"])
        total_size = sum(b.get("backup_size", 0) for b in self.manifest["backups"])
        total_files = sum(b.get("files_count", 0) for b in self.manifest["backups"])
        
        existing = sum(1 for b in self.manifest["backups"] if Path(b["path"]).exists())
        
        return {
            "total_backups": total_backups,
            "existing_backups": existing,
            "total_size": self._format_size(total_size),
            "total_files_backed_up": total_files,
            "backup_directory": str(self.backup_dir.absolute())
        }


def run_backup_manager():
    """Ejecuta el gestor de backups interactivo."""
    print("\n" + "="*60)
    print("  GESTOR DE BACKUPS")
    print("="*60)
    
    backup_dir = input("\n  Directorio de backups (Enter=backups): ").strip()
    backup_dir = backup_dir or "backups"
    
    manager = BackupManager(backup_dir)
    
    while True:
        print("\n  Opciones:")
        print("  1. Crear nuevo backup")
        print("  2. Listar backups")
        print("  3. Restaurar backup")
        print("  4. Verificar backup")
        print("  5. Eliminar backup")
        print("  6. Ver estadísticas")
        print("  7. Volver")
        
        opcion = input("\n  Seleccione (1-7): ").strip()
        
        if opcion == "1":
            source = input("  Ruta a respaldar: ").strip()
            name = input("  Nombre del backup (Enter=auto): ").strip() or None
            
            print("\n  Tipo de compresión:")
            print("  1. ZIP (recomendado)")
            print("  2. TAR.GZ")
            print("  3. Sin compresión")
            comp_opt = input("  Seleccione (1-3): ").strip()
            
            compression = {"1": "zip", "2": "tar.gz", "3": "none"}.get(comp_opt, "zip")
            
            print("\n  Creando backup...")
            result = manager.create_backup(source, name, compression)
            
            if result["success"]:
                print(f"\n  ✓ Backup creado exitosamente")
                print(f"    Ubicación: {result['backup_path']}")
                print(f"    Archivos: {result['files_count']}")
                print(f"    Tamaño original: {result['original_size']}")
                print(f"    Tamaño backup: {result['backup_size']}")
                print(f"    Compresión: {result['compression_ratio']}")
                print(f"    Duración: {result['duration']}")
            else:
                print(f"\n  ✗ Error: {result['error']}")
        
        elif opcion == "2":
            backups = manager.list_backups()
            
            if not backups:
                print("\n  No hay backups registrados")
            else:
                print(f"\n  {'ID':>4}  {'NOMBRE':<35}  {'FECHA':<15}  {'TAMAÑO':<12}  {'ESTADO'}")
                print("  " + "-"*80)
                for b in backups:
                    status = "✓" if b['exists'] else "✗ NO ENCONTRADO"
                    print(f"  {b['id']:>4}  {b['name'][:35]:<35}  {b['created']:<15}  {b['size']:<12}  {status}")
        
        elif opcion == "3":
            backup_id = input("  ID del backup a restaurar: ").strip()
            restore_path = input("  Ruta de restauración (Enter=auto): ").strip() or None
            
            if backup_id.isdigit():
                print("\n  Restaurando...")
                result = manager.restore_backup(int(backup_id), restore_path)
                
                if result["success"]:
                    print(f"\n  ✓ Backup restaurado en: {result['restored_to']}")
                else:
                    print(f"\n  ✗ Error: {result['error']}")
            else:
                print("  ID inválido")
        
        elif opcion == "4":
            backup_id = input("  ID del backup a verificar: ").strip()
            
            if backup_id.isdigit():
                result = manager.verify_backup(int(backup_id))
                
                if result.get("valid"):
                    print(f"\n  ✓ {result['message']}")
                else:
                    print(f"\n  ✗ {result.get('message', result.get('error'))}")
            else:
                print("  ID inválido")
        
        elif opcion == "5":
            backup_id = input("  ID del backup a eliminar: ").strip()
            confirm = input("  ¿Confirmar eliminación? (s/n): ").strip().lower()
            
            if confirm == 's' and backup_id.isdigit():
                result = manager.delete_backup(int(backup_id))
                if result["success"]:
                    print(f"\n  ✓ {result['message']}")
                else:
                    print(f"\n  ✗ {result['error']}")
        
        elif opcion == "6":
            stats = manager.get_backup_stats()
            print(f"\n  Estadísticas de Backups")
            print(f"  {'-'*40}")
            print(f"  Total de backups: {stats['total_backups']}")
            print(f"  Backups existentes: {stats['existing_backups']}")
            print(f"  Espacio utilizado: {stats['total_size']}")
            print(f"  Archivos respaldados: {stats['total_files_backed_up']}")
            print(f"  Directorio: {stats['backup_directory']}")
        
        elif opcion == "7":
            break


if __name__ == "__main__":
    run_backup_manager()
