"""File management schemas."""

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class FileType(str, Enum):
    """File type enumeration."""
    
    FILE = "file"
    DIRECTORY = "directory"
    SYMLINK = "symlink"


class FileInfo(BaseModel):
    """File or directory information."""
    
    name: str = Field(..., description="File or directory name")
    path: str = Field(..., description="Full path")
    type: FileType = Field(..., description="Type: file, directory, or symlink")
    size: int = Field(0, description="File size in bytes")
    mode: str = Field(..., description="Permission mode (e.g., 'rwxr-xr-x')")
    mode_octal: str = Field(..., description="Permission mode in octal (e.g., '755')")
    owner: str = Field(..., description="Owner username")
    group: str = Field(..., description="Group name")
    modified_at: datetime = Field(..., description="Last modification time")
    is_hidden: bool = Field(False, description="Whether the file is hidden")
    extension: Optional[str] = Field(None, description="File extension")
    mime_type: Optional[str] = Field(None, description="MIME type")


class FileListRequest(BaseModel):
    """Request for listing directory contents."""
    
    path: str = Field("/", description="Directory path to list")
    show_hidden: bool = Field(False, description="Include hidden files")
    sort_by: str = Field("name", description="Sort field: name, size, modified_at, type")
    sort_order: str = Field("asc", description="Sort order: asc or desc")


class FileListResponse(BaseModel):
    """Response containing directory listing."""
    
    path: str = Field(..., description="Current directory path")
    parent: Optional[str] = Field(None, description="Parent directory path")
    items: list[FileInfo] = Field(default_factory=list, description="List of files and directories")
    total: int = Field(0, description="Total number of items")


class FileReadRequest(BaseModel):
    """Request for reading file content."""
    
    path: str = Field(..., description="File path to read")
    encoding: str = Field("utf-8", description="File encoding")
    max_size: int = Field(1024 * 1024, description="Maximum file size to read (bytes)")


class FileReadResponse(BaseModel):
    """Response containing file content."""
    
    path: str = Field(..., description="File path")
    content: str = Field(..., description="File content")
    size: int = Field(..., description="File size in bytes")
    encoding: str = Field(..., description="File encoding used")
    mime_type: Optional[str] = Field(None, description="MIME type")


class FileCreateRequest(BaseModel):
    """Request for creating a file or directory."""
    
    path: str = Field(..., description="Path where to create")
    name: str = Field(..., description="Name of the file or directory")
    is_directory: bool = Field(False, description="Create a directory instead of file")
    content: Optional[str] = Field(None, description="Initial file content (for files only)")


class FileWriteRequest(BaseModel):
    """Request for writing file content."""
    
    path: str = Field(..., description="File path to write")
    content: str = Field(..., description="Content to write")
    encoding: str = Field("utf-8", description="File encoding")
    create_if_not_exists: bool = Field(True, description="Create file if it doesn't exist")


class FileRenameRequest(BaseModel):
    """Request for renaming a file or directory."""
    
    path: str = Field(..., description="Current file/directory path")
    new_name: str = Field(..., description="New name (not full path)")


class FileMoveRequest(BaseModel):
    """Request for moving files or directories."""
    
    source: str = Field(..., description="Source path")
    destination: str = Field(..., description="Destination directory path")
    overwrite: bool = Field(False, description="Overwrite if destination exists")


class FileCopyRequest(BaseModel):
    """Request for copying files or directories."""
    
    source: str = Field(..., description="Source path")
    destination: str = Field(..., description="Destination directory path")
    overwrite: bool = Field(False, description="Overwrite if destination exists")


class FileDeleteRequest(BaseModel):
    """Request for deleting files or directories."""
    
    paths: list[str] = Field(..., description="List of paths to delete")
    recursive: bool = Field(False, description="Recursively delete directories")


class FilePermissionRequest(BaseModel):
    """Request for changing file permissions."""
    
    path: str = Field(..., description="File or directory path")
    mode: str = Field(..., description="Permission mode in octal (e.g., '755')")
    recursive: bool = Field(False, description="Apply recursively to directories")


class FileSearchRequest(BaseModel):
    """Request for searching files."""
    
    path: str = Field("/", description="Directory to search in")
    pattern: str = Field(..., description="Search pattern (supports wildcards)")
    recursive: bool = Field(True, description="Search recursively")
    include_hidden: bool = Field(False, description="Include hidden files")
    file_type: Optional[FileType] = Field(None, description="Filter by file type")
    max_results: int = Field(100, description="Maximum number of results")


class FileSearchResponse(BaseModel):
    """Response containing search results."""
    
    results: list[FileInfo] = Field(default_factory=list, description="Matching files")
    total: int = Field(0, description="Total matches found")
    truncated: bool = Field(False, description="Whether results were truncated")


class FileCompressRequest(BaseModel):
    """Request for compressing files."""
    
    paths: list[str] = Field(..., description="Paths to compress")
    destination: str = Field(..., description="Output archive path")
    format: str = Field("zip", description="Archive format: zip, tar, tar.gz, tar.bz2")


class FileDecompressRequest(BaseModel):
    """Request for decompressing archives."""
    
    path: str = Field(..., description="Archive file path")
    destination: str = Field(..., description="Destination directory")
    overwrite: bool = Field(False, description="Overwrite existing files")


class FileOperationResponse(BaseModel):
    """Generic response for file operations."""
    
    success: bool = Field(..., description="Whether the operation succeeded")
    message: str = Field(..., description="Operation result message")
    path: Optional[str] = Field(None, description="Affected path")
