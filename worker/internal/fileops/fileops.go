// Package fileops provides file system operations for the worker agent.
package fileops

import (
	"fmt"
	"os"
	"path/filepath"
	"strings"
)

// ValidatePath checks if the given path is within the allowed base directory.
// Returns the cleaned absolute path if valid, or an error if the path is invalid.
func ValidatePath(basePath, targetPath string) (string, error) {
	// Clean and resolve the base path
	absBase, err := filepath.Abs(basePath)
	if err != nil {
		return "", fmt.Errorf("invalid base path: %w", err)
	}

	// Build full path
	var fullPath string
	if filepath.IsAbs(targetPath) {
		fullPath = targetPath
	} else {
		fullPath = filepath.Join(absBase, targetPath)
	}

	// Clean and resolve the target path
	absTarget, err := filepath.Abs(fullPath)
	if err != nil {
		return "", fmt.Errorf("invalid target path: %w", err)
	}

	// Ensure target is within base directory (prevent path traversal)
	if !strings.HasPrefix(absTarget, absBase+string(os.PathSeparator)) && absTarget != absBase {
		return "", fmt.Errorf("path traversal detected: %s is outside %s", absTarget, absBase)
	}

	return absTarget, nil
}

// EnsureDir creates a directory and all parent directories if they don't exist.
func EnsureDir(path string) error {
	return os.MkdirAll(path, 0755)
}

// PathExists checks if a path exists.
func PathExists(path string) bool {
	_, err := os.Stat(path)
	return err == nil
}

// RemoveAll removes a path and all its contents.
func RemoveAll(path string) error {
	return os.RemoveAll(path)
}

// GetPathInfo returns information about a path.
type PathInfo struct {
	Path    string `json:"path"`
	IsDir   bool   `json:"is_dir"`
	Size    int64  `json:"size"`
	ModTime int64  `json:"mod_time"`
	Mode    string `json:"mode"`
}

// GetInfo returns information about a file or directory.
func GetInfo(path string) (*PathInfo, error) {
	info, err := os.Stat(path)
	if err != nil {
		return nil, err
	}

	return &PathInfo{
		Path:    path,
		IsDir:   info.IsDir(),
		Size:    info.Size(),
		ModTime: info.ModTime().Unix(),
		Mode:    info.Mode().String(),
	}, nil
}
