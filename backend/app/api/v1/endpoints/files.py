"""File management API endpoints."""

import os
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query, status
from fastapi.responses import FileResponse, StreamingResponse

from app.api.deps import get_current_active_user
from app.models.user import User
from app.schemas.files import (
    FileListRequest,
    FileListResponse,
    FileReadRequest,
    FileReadResponse,
    FileCreateRequest,
    FileWriteRequest,
    FileRenameRequest,
    FileMoveRequest,
    FileCopyRequest,
    FileDeleteRequest,
    FilePermissionRequest,
    FileSearchRequest,
    FileSearchResponse,
    FileCompressRequest,
    FileDecompressRequest,
    FileOperationResponse,
    FileInfo,
)
from app.services.file_service import file_service

router = APIRouter()


@router.get("/list", response_model=FileListResponse)
async def list_directory(
    path: str = Query("/", description="Directory path to list"),
    show_hidden: bool = Query(False, description="Include hidden files"),
    sort_by: str = Query("name", description="Sort field: name, size, modified_at, type"),
    sort_order: str = Query("asc", description="Sort order: asc or desc"),
    current_user: User = Depends(get_current_active_user),
):
    """
    List contents of a directory.
    
    Returns a list of files and directories in the specified path,
    with support for sorting and filtering hidden files.
    """
    return file_service.list_directory(
        path=path,
        show_hidden=show_hidden,
        sort_by=sort_by,
        sort_order=sort_order,
    )


@router.get("/read", response_model=FileReadResponse)
async def read_file(
    path: str = Query(..., description="File path to read"),
    encoding: str = Query("utf-8", description="File encoding"),
    max_size: int = Query(1024 * 1024, description="Maximum file size in bytes"),
    current_user: User = Depends(get_current_active_user),
):
    """
    Read file content.
    
    Returns the content of a text file with the specified encoding.
    Binary files should be downloaded instead.
    """
    return file_service.read_file(
        path=path,
        encoding=encoding,
        max_size=max_size,
    )


@router.post("/create", response_model=FileOperationResponse)
async def create_file_or_directory(
    request: FileCreateRequest,
    current_user: User = Depends(get_current_active_user),
):
    """
    Create a new file or directory.
    
    Creates a new file with optional initial content, or an empty directory.
    """
    return file_service.create(
        path=request.path,
        name=request.name,
        is_directory=request.is_directory,
        content=request.content,
    )


@router.put("/write", response_model=FileOperationResponse)
async def write_file(
    request: FileWriteRequest,
    current_user: User = Depends(get_current_active_user),
):
    """
    Write content to a file.
    
    Saves content to an existing file or creates a new one.
    """
    return file_service.write_file(
        path=request.path,
        content=request.content,
        encoding=request.encoding,
        create_if_not_exists=request.create_if_not_exists,
    )


@router.post("/upload", response_model=FileOperationResponse)
async def upload_file(
    path: str = Query(..., description="Directory to upload to"),
    file: UploadFile = File(..., description="File to upload"),
    overwrite: bool = Query(False, description="Overwrite if exists"),
    current_user: User = Depends(get_current_active_user),
):
    """
    Upload a file.
    
    Uploads a file to the specified directory.
    """
    from pathlib import Path
    
    # Validate directory
    resolved_path = file_service._resolve_path(path)
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
    
    target_path = resolved_path / file.filename
    
    if target_path.exists() and not overwrite:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"File already exists: {file.filename}"
        )
    
    try:
        content = await file.read()
        target_path.write_bytes(content)
    except PermissionError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission denied"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Upload failed: {str(e)}"
        )
    
    return FileOperationResponse(
        success=True,
        message="File uploaded successfully",
        path=str(target_path),
    )


@router.get("/download")
async def download_file(
    path: str = Query(..., description="File path to download"),
    current_user: User = Depends(get_current_active_user),
):
    """
    Download a file.
    
    Returns the file as a downloadable attachment.
    """
    resolved_path = file_service._resolve_path(path)
    
    if not resolved_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"File not found: {path}"
        )
    
    if resolved_path.is_dir():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot download directory. Compress it first."
        )
    
    return FileResponse(
        path=str(resolved_path),
        filename=resolved_path.name,
        media_type="application/octet-stream",
    )


@router.put("/rename", response_model=FileOperationResponse)
async def rename_file(
    request: FileRenameRequest,
    current_user: User = Depends(get_current_active_user),
):
    """
    Rename a file or directory.
    
    Renames the file or directory to a new name (not path).
    """
    return file_service.rename(
        path=request.path,
        new_name=request.new_name,
    )


@router.put("/move", response_model=FileOperationResponse)
async def move_file(
    request: FileMoveRequest,
    current_user: User = Depends(get_current_active_user),
):
    """
    Move a file or directory.
    
    Moves the source to the destination directory.
    """
    return file_service.move(
        source=request.source,
        destination=request.destination,
        overwrite=request.overwrite,
    )


@router.put("/copy", response_model=FileOperationResponse)
async def copy_file(
    request: FileCopyRequest,
    current_user: User = Depends(get_current_active_user),
):
    """
    Copy a file or directory.
    
    Copies the source to the destination directory.
    """
    return file_service.copy(
        source=request.source,
        destination=request.destination,
        overwrite=request.overwrite,
    )


@router.delete("/delete", response_model=FileOperationResponse)
async def delete_files(
    request: FileDeleteRequest,
    current_user: User = Depends(get_current_active_user),
):
    """
    Delete files or directories.
    
    Deletes multiple files or directories. Use recursive=true for non-empty directories.
    """
    return file_service.delete(
        paths=request.paths,
        recursive=request.recursive,
    )


@router.get("/info", response_model=FileInfo)
async def get_file_info(
    path: str = Query(..., description="File or directory path"),
    current_user: User = Depends(get_current_active_user),
):
    """
    Get file or directory information.
    
    Returns detailed information including permissions, owner, size, and timestamps.
    """
    return file_service.get_info(path)


@router.put("/permission", response_model=FileOperationResponse)
async def change_permission(
    request: FilePermissionRequest,
    current_user: User = Depends(get_current_active_user),
):
    """
    Change file or directory permissions.
    
    Changes permissions using octal mode (e.g., '755', '644').
    """
    # Only admins can change permissions
    if current_user.role not in ("admin", "superadmin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can change file permissions"
        )
    
    return file_service.change_permission(
        path=request.path,
        mode=request.mode,
        recursive=request.recursive,
    )


@router.post("/search", response_model=FileSearchResponse)
async def search_files(
    request: FileSearchRequest,
    current_user: User = Depends(get_current_active_user),
):
    """
    Search for files.
    
    Searches for files matching a pattern (supports wildcards like *, ?).
    """
    return file_service.search(
        path=request.path,
        pattern=request.pattern,
        recursive=request.recursive,
        include_hidden=request.include_hidden,
        file_type=request.file_type,
        max_results=request.max_results,
    )


@router.post("/compress", response_model=FileOperationResponse)
async def compress_files(
    request: FileCompressRequest,
    current_user: User = Depends(get_current_active_user),
):
    """
    Compress files into an archive.
    
    Supports formats: zip, tar, tar.gz, tar.bz2
    """
    return file_service.compress(
        paths=request.paths,
        destination=request.destination,
        format=request.format,
    )


@router.post("/decompress", response_model=FileOperationResponse)
async def decompress_archive(
    request: FileDecompressRequest,
    current_user: User = Depends(get_current_active_user),
):
    """
    Decompress an archive.
    
    Extracts contents of zip, tar, tar.gz, or tar.bz2 archives.
    """
    return file_service.decompress(
        path=request.path,
        destination=request.destination,
        overwrite=request.overwrite,
    )
