// Package scanner provides dataset scanning functionality.
package scanner

import (
	"fmt"
	"os"
	"path/filepath"
	"strings"

	"github.com/YangYuS8/mlsmanager-worker-agent/internal/client"
)

// Scanner scans directories for datasets.
type Scanner struct {
	formatMap map[string]string
}

// NewScanner creates a new dataset scanner.
func NewScanner() *Scanner {
	return &Scanner{
		formatMap: map[string]string{
			".csv":      "csv",
			".parquet":  "parquet",
			".json":     "json",
			".jsonl":    "jsonl",
			".tfrecord": "tfrecord",
			".tar":      "archive",
			".tar.gz":   "archive",
			".tgz":      "archive",
			".zip":      "archive",
			".jpg":      "images",
			".jpeg":     "images",
			".png":      "images",
			".gif":      "images",
			".bmp":      "images",
			".tiff":     "images",
		},
	}
}

// Scan scans the base path for datasets.
// Each subdirectory is treated as a separate dataset.
func (s *Scanner) Scan(basePath string) []client.DatasetInfo {
	var datasets []client.DatasetInfo

	// Check if path exists
	if _, err := os.Stat(basePath); os.IsNotExist(err) {
		fmt.Printf("[WARN] Dataset path does not exist: %s\n", basePath)
		return datasets
	}

	// List directories in base path
	entries, err := os.ReadDir(basePath)
	if err != nil {
		fmt.Printf("[ERROR] Failed to read dataset path: %v\n", err)
		return datasets
	}

	for _, entry := range entries {
		// Skip hidden directories and files
		if strings.HasPrefix(entry.Name(), ".") {
			continue
		}

		if !entry.IsDir() {
			continue
		}

		dirPath := filepath.Join(basePath, entry.Name())
		dataset := s.scanDirectory(dirPath, entry.Name())
		if dataset != nil {
			datasets = append(datasets, *dataset)
		}
	}

	return datasets
}

// scanDirectory scans a single directory as a dataset.
func (s *Scanner) scanDirectory(path, name string) *client.DatasetInfo {
	var totalSize int64
	var fileCount int
	formatCounts := make(map[string]int)

	err := filepath.Walk(path, func(filePath string, info os.FileInfo, err error) error {
		if err != nil {
			return nil // Skip errors, continue walking
		}

		if info.IsDir() {
			return nil
		}

		fileCount++
		totalSize += info.Size()

		// Detect format
		ext := strings.ToLower(filepath.Ext(filePath))
		fileName := strings.ToLower(info.Name())

		// Check for compound extensions like .tar.gz
		if strings.HasSuffix(fileName, ".tar.gz") {
			formatCounts["archive"]++
		} else if format, ok := s.formatMap[ext]; ok {
			formatCounts[format]++
		}

		return nil
	})

	if err != nil {
		fmt.Printf("[ERROR] Error scanning directory %s: %v\n", path, err)
		return nil
	}

	// Determine primary format
	var primaryFormat *string
	maxCount := 0
	for format, count := range formatCounts {
		if count > maxCount {
			maxCount = count
			f := format
			primaryFormat = &f
		}
	}

	absPath, _ := filepath.Abs(path)
	description := fmt.Sprintf("Auto-scanned dataset with %d files", fileCount)

	return &client.DatasetInfo{
		Name:        name,
		LocalPath:   absPath,
		SizeBytes:   &totalSize,
		FileCount:   &fileCount,
		Format:      primaryFormat,
		Description: &description,
	}
}
