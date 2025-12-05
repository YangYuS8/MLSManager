// Package sysinfo provides system information collection utilities.
package sysinfo

import (
	"os/exec"
	"runtime"
	"strings"

	"github.com/shirou/gopsutil/v4/cpu"
	"github.com/shirou/gopsutil/v4/disk"
	"github.com/shirou/gopsutil/v4/mem"
)

// SystemInfo holds system resource information.
type SystemInfo struct {
	CPUCount       int     `json:"cpu_count"`
	MemoryTotalGB  *int    `json:"memory_total_gb"`
	GPUCount       int     `json:"gpu_count"`
	GPUInfo        *string `json:"gpu_info"`
	StorageTotalGB *int    `json:"storage_total_gb"`
	StorageUsedGB  *int    `json:"storage_used_gb"`
}

// Collect gathers system information.
func Collect(storagePath string) *SystemInfo {
	info := &SystemInfo{
		CPUCount: runtime.NumCPU(),
		GPUCount: 0,
	}

	// Memory info
	if vmStat, err := mem.VirtualMemory(); err == nil {
		memGB := int(vmStat.Total / (1024 * 1024 * 1024))
		info.MemoryTotalGB = &memGB
	}

	// GPU info via nvidia-smi
	if gpuInfo, gpuCount := getGPUInfo(); gpuCount > 0 {
		info.GPUCount = gpuCount
		info.GPUInfo = &gpuInfo
	}

	// Storage info
	if usage, err := disk.Usage(storagePath); err == nil {
		totalGB := int(usage.Total / (1024 * 1024 * 1024))
		usedGB := int(usage.Used / (1024 * 1024 * 1024))
		info.StorageTotalGB = &totalGB
		info.StorageUsedGB = &usedGB
	}

	return info
}

// getGPUInfo queries nvidia-smi for GPU information.
func getGPUInfo() (string, int) {
	cmd := exec.Command("nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader")
	output, err := cmd.Output()
	if err != nil {
		return "", 0
	}

	outputStr := strings.TrimSpace(string(output))
	if outputStr == "" {
		return "", 0
	}

	lines := strings.Split(outputStr, "\n")
	count := 0
	for _, line := range lines {
		if strings.TrimSpace(line) != "" {
			count++
		}
	}

	return outputStr, count
}

// GetCPUUsage returns current CPU usage percentage.
func GetCPUUsage() (float64, error) {
	percentages, err := cpu.Percent(0, false)
	if err != nil {
		return 0, err
	}
	if len(percentages) > 0 {
		return percentages[0], nil
	}
	return 0, nil
}
