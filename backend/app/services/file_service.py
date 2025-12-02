"""File management service."""

import grp
import mimetypes
import os
import pwd
import shutil
import stat
import zipfile
import tarfile
from datetime import datetime
from fnmatch import fnmatch
from pathlib import Path
from typing import Optional

from fastapi import HTTPException, status

from app.schemas.files import (
    FileType,
    FileInfo,
    FileListResponse,
    FileReadResponse,
    FileSearchResponse,
    FileOperationResponse,
)


class FileService:
    """Service for file system operations."""
    
    def __init__(self, base_path: str = "/"):
        """Initialize file service with base path restriction."""
        self.base_path = Path(base_path).resolve()
    
    def _resolve_path(self, path: str) -> Path:
        """
        Resolve and validate path to prevent directory traversal.
        
        Args:
            path: The path to resolve
            
        Returns:
            Resolved absolute Path object
            
        Raises:
            HTTPException: If path is outside base_path
        """
        # Normalize and resolve the path
        resolved = (self.base_path / path.lstrip("/")).resolve()
        
        # Check if resolved path is within base_path
        try:
            resolved.relative_to(self.base_path)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: path is outside allowed directory"
            )
        
        return resolved
    
    def _get_file_info(self, path: Path) -> FileInfo:
        """Get detailed information about a file or directory."""
        try:
            stat_info = path.lstat()
            
            # Determine file type
            if path.is_symlink():
                file_type = FileType.SYMLINK
            elif path.is_dir():
                file_type = FileType.DIRECTORY
            else:
                file_type = FileType.FILE
            
            # Get permission string
            mode = stat_info.st_mode
            mode_str = stat.filemode(mode)
            mode_octal = oct(stat.S_IMODE(mode))[2:]
            
            # Get owner and group
            try:
                owner = pwd.getpwuid(stat_info.st_uid).pw_name
            except KeyError:
                owner = str(stat_info.st_uid)
            
            try:
                group = grp.getgrgid(stat_info.st_gid).gr_name
            except KeyError:
                group = str(stat_info.st_gid)
            
            # Get file extension and MIME type
            extension = path.suffix.lstrip(".") if path.suffix else None
            mime_type = None
            if file_type == FileType.FILE:
                mime_type, _ = mimetypes.guess_type(str(path))
            
            return FileInfo(
                name=path.name,
                path=str(path),
                type=file_type,
                size=stat_info.st_size if file_type != FileType.DIRECTORY else 0,
                mode=mode_str,
                mode_octal=mode_octal,
                owner=owner,
                group=group,
                modified_at=datetime.fromtimestamp(stat_info.st_mtime),
                is_hidden=path.name.startswith("."),
                extension=extension,
                mime_type=mime_type,
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get file info: {str(e)}"
            )
    
    def list_directory(
        self,
        path: str,
        show_hidden: bool = False,
        sort_by: str = "name",
        sort_order: str = "asc",
    ) -> FileListResponse:
        """List contents of a directory."""
        resolved_path = self._resolve_path(path)
        
        if not resolved_path.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Directory not found: {path}"
            )
        
        if not resolved_path.is_dir():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Not a directory: {path}"
            )
        
        items = []
        try:
            for entry in resolved_path.iterdir():
                if not show_hidden and entry.name.startswith("."):
                    continue
                
                try:
                    items.append(self._get_file_info(entry))
                except Exception:
                    # Skip files we can't access
                    continue
        except PermissionError:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied: {path}"
            )
        
        # Sort items
        reverse = sort_order.lower() == "desc"
        if sort_by == "name":
            items.sort(key=lambda x: (x.type != FileType.DIRECTORY, x.name.lower()), reverse=reverse)
        elif sort_by == "size":
            items.sort(key=lambda x: (x.type != FileType.DIRECTORY, x.size), reverse=reverse)
        elif sort_by == "modified_at":
            items.sort(key=lambda x: (x.type != FileType.DIRECTORY, x.modified_at), reverse=reverse)
        elif sort_by == "type":
            items.sort(key=lambda x: (x.type.value, x.name.lower()), reverse=reverse)
        
        # Calculate parent path
        parent = None
        if resolved_path != self.base_path:
            parent = str(resolved_path.parent)
        
        return FileListResponse(
            path=str(resolved_path),
            parent=parent,
            items=items,
            total=len(items),
        )
    
    def read_file(
        self,
        path: str,
        encoding: str = "utf-8",
        max_size: int = 1024 * 1024,
    ) -> FileReadResponse:
        """Read file content."""
        resolved_path = self._resolve_path(path)
        
        if not resolved_path.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"File not found: {path}"
            )
        
        if resolved_path.is_dir():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot read directory: {path}"
            )
        
        file_size = resolved_path.stat().st_size
        if file_size > max_size:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File too large: {file_size} bytes (max: {max_size})"
            )
        
        try:
            content = resolved_path.read_text(encoding=encoding)
        except UnicodeDecodeError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot decode file with encoding: {encoding}"
            )
        except PermissionError:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied: {path}"
            )
        
        mime_type, _ = mimetypes.guess_type(str(resolved_path))
        
        return FileReadResponse(
            path=str(resolved_path),
            content=content,
            size=file_size,
            encoding=encoding,
            mime_type=mime_type,
        )
    
    def write_file(
        self,
        path: str,
        content: str,
        encoding: str = "utf-8",
        create_if_not_exists: bool = True,
    ) -> FileOperationResponse:
        """Write content to a file."""
        resolved_path = self._resolve_path(path)
        
        if not create_if_not_exists and not resolved_path.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"File not found: {path}"
            )
        
        if resolved_path.exists() and resolved_path.is_dir():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot write to directory: {path}"
            )
        
        try:
            resolved_path.parent.mkdir(parents=True, exist_ok=True)
            resolved_path.write_text(content, encoding=encoding)
        except PermissionError:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied: {path}"
            )
        
        return FileOperationResponse(
            success=True,
            message="File saved successfully",
            path=str(resolved_path),
        )
    
    def create(
        self,
        path: str,
        name: str,
        is_directory: bool = False,
        content: Optional[str] = None,
    ) -> FileOperationResponse:
        """Create a new file or directory."""
        resolved_path = self._resolve_path(path)
        target_path = resolved_path / name
        
        # Validate the target path
        self._resolve_path(str(target_path.relative_to(self.base_path)))
        
        if target_path.exists():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Already exists: {name}"
            )
        
        try:
            if is_directory:
                target_path.mkdir(parents=True)
                message = "Directory created successfully"
            else:
                target_path.parent.mkdir(parents=True, exist_ok=True)
                target_path.write_text(content or "", encoding="utf-8")
                message = "File created successfully"
        except PermissionError:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied: {path}"
            )
        
        return FileOperationResponse(
            success=True,
            message=message,
            path=str(target_path),
        )
    
    def rename(self, path: str, new_name: str) -> FileOperationResponse:
        """Rename a file or directory."""
        resolved_path = self._resolve_path(path)
        
        if not resolved_path.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Not found: {path}"
            )
        
        new_path = resolved_path.parent / new_name
        
        # Validate new path
        self._resolve_path(str(new_path.relative_to(self.base_path)))
        
        if new_path.exists():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Already exists: {new_name}"
            )
        
        try:
            resolved_path.rename(new_path)
        except PermissionError:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied: {path}"
            )
        
        return FileOperationResponse(
            success=True,
            message="Renamed successfully",
            path=str(new_path),
        )
    
    def move(
        self,
        source: str,
        destination: str,
        overwrite: bool = False,
    ) -> FileOperationResponse:
        """Move a file or directory."""
        source_path = self._resolve_path(source)
        dest_path = self._resolve_path(destination)
        
        if not source_path.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Source not found: {source}"
            )
        
        if not dest_path.is_dir():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Destination is not a directory: {destination}"
            )
        
        target_path = dest_path / source_path.name
        
        if target_path.exists() and not overwrite:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Destination already exists: {target_path.name}"
            )
        
        try:
            if target_path.exists():
                if target_path.is_dir():
                    shutil.rmtree(target_path)
                else:
                    target_path.unlink()
            shutil.move(str(source_path), str(target_path))
        except PermissionError:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Permission denied"
            )
        
        return FileOperationResponse(
            success=True,
            message="Moved successfully",
            path=str(target_path),
        )
    
    def copy(
        self,
        source: str,
        destination: str,
        overwrite: bool = False,
    ) -> FileOperationResponse:
        """Copy a file or directory."""
        source_path = self._resolve_path(source)
        dest_path = self._resolve_path(destination)
        
        if not source_path.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Source not found: {source}"
            )
        
        if not dest_path.is_dir():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Destination is not a directory: {destination}"
            )
        
        target_path = dest_path / source_path.name
        
        if target_path.exists() and not overwrite:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Destination already exists: {target_path.name}"
            )
        
        try:
            if source_path.is_dir():
                if target_path.exists():
                    shutil.rmtree(target_path)
                shutil.copytree(str(source_path), str(target_path))
            else:
                shutil.copy2(str(source_path), str(target_path))
        except PermissionError:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Permission denied"
            )
        
        return FileOperationResponse(
            success=True,
            message="Copied successfully",
            path=str(target_path),
        )
    
    def delete(
        self,
        paths: list[str],
        recursive: bool = False,
    ) -> FileOperationResponse:
        """Delete files or directories."""
        deleted = []
        failed = []
        
        for path in paths:
            try:
                resolved_path = self._resolve_path(path)
                
                if not resolved_path.exists():
                    failed.append(f"{path}: not found")
                    continue
                
                if resolved_path.is_dir():
                    if not recursive:
                        # Check if directory is empty
                        if any(resolved_path.iterdir()):
                            failed.append(f"{path}: directory not empty")
                            continue
                        resolved_path.rmdir()
                    else:
                        shutil.rmtree(resolved_path)
                else:
                    resolved_path.unlink()
                
                deleted.append(path)
            except PermissionError:
                failed.append(f"{path}: permission denied")
            except Exception as e:
                failed.append(f"{path}: {str(e)}")
        
        if failed:
            return FileOperationResponse(
                success=len(deleted) > 0,
                message=f"Deleted {len(deleted)} item(s), {len(failed)} failed: {', '.join(failed)}",
                path=None,
            )
        
        return FileOperationResponse(
            success=True,
            message=f"Deleted {len(deleted)} item(s) successfully",
            path=None,
        )
    
    def get_info(self, path: str) -> FileInfo:
        """Get detailed information about a file or directory."""
        resolved_path = self._resolve_path(path)
        
        if not resolved_path.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Not found: {path}"
            )
        
        return self._get_file_info(resolved_path)
    
    def change_permission(
        self,
        path: str,
        mode: str,
        recursive: bool = False,
    ) -> FileOperationResponse:
        """Change file or directory permissions."""
        resolved_path = self._resolve_path(path)
        
        if not resolved_path.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Not found: {path}"
            )
        
        try:
            mode_int = int(mode, 8)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid permission mode: {mode}"
            )
        
        try:
            if recursive and resolved_path.is_dir():
                for item in resolved_path.rglob("*"):
                    os.chmod(item, mode_int)
                os.chmod(resolved_path, mode_int)
            else:
                os.chmod(resolved_path, mode_int)
        except PermissionError:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Permission denied"
            )
        
        return FileOperationResponse(
            success=True,
            message="Permissions changed successfully",
            path=str(resolved_path),
        )
    
    def search(
        self,
        path: str,
        pattern: str,
        recursive: bool = True,
        include_hidden: bool = False,
        file_type: Optional[FileType] = None,
        max_results: int = 100,
    ) -> FileSearchResponse:
        """Search for files matching a pattern."""
        resolved_path = self._resolve_path(path)
        
        if not resolved_path.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Directory not found: {path}"
            )
        
        if not resolved_path.is_dir():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Not a directory: {path}"
            )
        
        results = []
        truncated = False
        
        try:
            if recursive:
                iterator = resolved_path.rglob("*")
            else:
                iterator = resolved_path.iterdir()
            
            for item in iterator:
                if len(results) >= max_results:
                    truncated = True
                    break
                
                # Skip hidden files if not included
                if not include_hidden and any(part.startswith(".") for part in item.parts):
                    continue
                
                # Check pattern match
                if not fnmatch(item.name, pattern):
                    continue
                
                # Filter by file type
                if file_type is not None:
                    if file_type == FileType.DIRECTORY and not item.is_dir():
                        continue
                    if file_type == FileType.FILE and not item.is_file():
                        continue
                    if file_type == FileType.SYMLINK and not item.is_symlink():
                        continue
                
                try:
                    results.append(self._get_file_info(item))
                except Exception:
                    continue
        except PermissionError:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied: {path}"
            )
        
        return FileSearchResponse(
            results=results,
            total=len(results),
            truncated=truncated,
        )
    
    def compress(
        self,
        paths: list[str],
        destination: str,
        format: str = "zip",
    ) -> FileOperationResponse:
        """Compress files into an archive."""
        dest_path = self._resolve_path(destination)
        
        if dest_path.exists():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Destination already exists: {destination}"
            )
        
        source_paths = []
        for path in paths:
            resolved = self._resolve_path(path)
            if not resolved.exists():
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Source not found: {path}"
                )
            source_paths.append(resolved)
        
        try:
            if format == "zip":
                with zipfile.ZipFile(dest_path, "w", zipfile.ZIP_DEFLATED) as zf:
                    for source in source_paths:
                        if source.is_dir():
                            for item in source.rglob("*"):
                                zf.write(item, item.relative_to(source.parent))
                        else:
                            zf.write(source, source.name)
            
            elif format in ("tar", "tar.gz", "tar.bz2"):
                mode_map = {"tar": "w", "tar.gz": "w:gz", "tar.bz2": "w:bz2"}
                with tarfile.open(dest_path, mode_map[format]) as tf:
                    for source in source_paths:
                        tf.add(source, source.name)
            
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Unsupported format: {format}"
                )
        except PermissionError:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Permission denied"
            )
        
        return FileOperationResponse(
            success=True,
            message="Compressed successfully",
            path=str(dest_path),
        )
    
    def decompress(
        self,
        path: str,
        destination: str,
        overwrite: bool = False,
    ) -> FileOperationResponse:
        """Decompress an archive."""
        source_path = self._resolve_path(path)
        dest_path = self._resolve_path(destination)
        
        if not source_path.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Archive not found: {path}"
            )
        
        if not dest_path.exists():
            dest_path.mkdir(parents=True)
        elif not dest_path.is_dir():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Destination is not a directory: {destination}"
            )
        
        try:
            # Try ZIP first
            if zipfile.is_zipfile(source_path):
                with zipfile.ZipFile(source_path, "r") as zf:
                    zf.extractall(dest_path)
            
            # Try TAR formats
            elif tarfile.is_tarfile(source_path):
                with tarfile.open(source_path, "r:*") as tf:
                    tf.extractall(dest_path)
            
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Unsupported archive format"
                )
        except PermissionError:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Permission denied"
            )
        
        return FileOperationResponse(
            success=True,
            message="Decompressed successfully",
            path=str(dest_path),
        )


# Create default instance with root access (should be configured per deployment)
file_service = FileService(base_path="/")
