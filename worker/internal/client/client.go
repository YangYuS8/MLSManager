// Package client provides HTTP client for communicating with master node.
package client

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"time"

	"github.com/YangYuS8/mlsmanager-worker/internal/config"
	"github.com/YangYuS8/mlsmanager-worker/internal/sysinfo"
)

// MasterClient communicates with the master node.
type MasterClient struct {
	cfg        *config.Config
	httpClient *http.Client
	token      string
	nodeID     string // node_id string, not database id
}

// NewMasterClient creates a new master client.
func NewMasterClient(cfg *config.Config) *MasterClient {
	token := cfg.LoadToken()
	c := &MasterClient{
		cfg: cfg,
		httpClient: &http.Client{
			Timeout: 30 * time.Second,
		},
		token: token,
	}
	// If we have a saved token, we're already registered with this node_id
	if token != "" {
		c.nodeID = cfg.NodeName
	}
	return c
}

// NodeID returns the registered node ID.
func (c *MasterClient) NodeID() string {
	return c.nodeID
}

// Token returns the current agent token.
func (c *MasterClient) Token() string {
	return c.token
}

// RegisterRequest is the payload for node registration.
type RegisterRequest struct {
	NodeID         string  `json:"node_id"`
	Name           string  `json:"name"`
	Host           string  `json:"host"`
	Hostname       string  `json:"hostname,omitempty"`
	Port           int     `json:"port"`
	AgentPort      int     `json:"agent_port"`
	StoragePath    *string `json:"storage_path,omitempty"`
	CPUCount       int     `json:"cpu_count"`
	MemoryTotalGB  *int    `json:"memory_total_gb"`
	GPUCount       int     `json:"gpu_count"`
	GPUInfo        *string `json:"gpu_info"`
	StorageTotalGB *int    `json:"storage_total_gb"`
	StorageUsedGB  *int    `json:"storage_used_gb"`
}

// RegisterResponse is the response from node registration.
type RegisterResponse struct {
	Node    map[string]any `json:"node"`
	Token   string         `json:"token"`
	Message string         `json:"message"`
}

// Register registers this agent with the master node.
func (c *MasterClient) Register(ctx context.Context) error {
	sysInfo := sysinfo.Collect(c.cfg.StoragePath)

	// Determine the hostname for backend to reach this worker
	// In dev mode, use localhost; otherwise use actual hostname
	hostname := c.cfg.NodeHostname
	if c.cfg.DevMode {
		hostname = "localhost"
	}

	storagePath := c.cfg.StoragePath
	req := RegisterRequest{
		NodeID:         c.cfg.NodeName, // Use node name as ID
		Name:           c.cfg.NodeName,
		Host:           c.cfg.NodeHostname,
		Hostname:       hostname,
		Port:           8001,
		AgentPort:      c.cfg.APIPort,
		StoragePath:    &storagePath,
		CPUCount:       sysInfo.CPUCount,
		MemoryTotalGB:  sysInfo.MemoryTotalGB,
		GPUCount:       sysInfo.GPUCount,
		GPUInfo:        sysInfo.GPUInfo,
		StorageTotalGB: sysInfo.StorageTotalGB,
		StorageUsedGB:  sysInfo.StorageUsedGB,
	}

	var resp RegisterResponse
	err := c.doRequest(ctx, "POST", "/api/v1/nodes/register", req, &resp, false)
	if err != nil {
		return fmt.Errorf("registration failed: %w", err)
	}

	c.token = resp.Token
	// Use the node_id we sent (string), not database id
	c.nodeID = c.cfg.NodeName

	// Save token to file
	if err := c.cfg.SaveToken(c.token); err != nil {
		// Log warning but don't fail registration
		fmt.Printf("[WARN] Failed to save token: %v\n", err)
	}

	return nil
}

// HeartbeatRequest is the payload for heartbeat.
type HeartbeatRequest struct {
	Status         string  `json:"status"`
	CPUCount       int     `json:"cpu_count"`
	MemoryTotalGB  *int    `json:"memory_total_gb"`
	GPUCount       int     `json:"gpu_count"`
	GPUInfo        *string `json:"gpu_info"`
	StorageTotalGB *int    `json:"storage_total_gb"`
	StorageUsedGB  *int    `json:"storage_used_gb"`
}

// Heartbeat sends a heartbeat to the master node.
func (c *MasterClient) Heartbeat(ctx context.Context) error {
	if c.nodeID == "" {
		return fmt.Errorf("not registered")
	}

	sysInfo := sysinfo.Collect(c.cfg.StoragePath)

	req := HeartbeatRequest{
		Status:         "online",
		CPUCount:       sysInfo.CPUCount,
		MemoryTotalGB:  sysInfo.MemoryTotalGB,
		GPUCount:       sysInfo.GPUCount,
		GPUInfo:        sysInfo.GPUInfo,
		StorageTotalGB: sysInfo.StorageTotalGB,
		StorageUsedGB:  sysInfo.StorageUsedGB,
	}

	url := fmt.Sprintf("/api/v1/nodes/%s/heartbeat", c.nodeID)
	return c.doRequest(ctx, "POST", url, req, nil, true)
}

// Job represents a job from the master.
type Job struct {
	ID               int               `json:"id"`
	Name             string            `json:"name"`
	Command          string            `json:"command"`
	Environment      string            `json:"environment"`
	EnvConfig        map[string]any    `json:"env_config"`
	EnvironmentVars  map[string]string `json:"environment_vars"`
	WorkingDirectory string            `json:"working_directory"`
	TimeoutSeconds   int               `json:"timeout_seconds"`
}

// FetchPendingJobs fetches pending jobs from the master.
func (c *MasterClient) FetchPendingJobs(ctx context.Context) ([]Job, error) {
	var jobs []Job
	url := fmt.Sprintf("/api/v1/jobs/queue/%s", c.nodeID)
	err := c.doRequest(ctx, "GET", url, nil, &jobs, true)
	if err != nil {
		return nil, err
	}
	return jobs, nil
}

// JobStatusUpdate is the payload for updating job status.
type JobStatusUpdate struct {
	Status       string  `json:"status"`
	ExitCode     *int    `json:"exit_code,omitempty"`
	ErrorMessage *string `json:"error_message,omitempty"`
}

// UpdateJobStatus updates the status of a job.
func (c *MasterClient) UpdateJobStatus(ctx context.Context, jobID int, status string, exitCode *int, errorMsg *string) error {
	req := JobStatusUpdate{
		Status:       status,
		ExitCode:     exitCode,
		ErrorMessage: errorMsg,
	}

	url := fmt.Sprintf("/api/v1/jobs/%d/status", jobID)
	return c.doRequest(ctx, "POST", url, req, nil, true)
}

// DatasetInfo represents a scanned dataset.
type DatasetInfo struct {
	Name        string  `json:"name"`
	LocalPath   string  `json:"local_path"`
	SizeBytes   *int64  `json:"size_bytes,omitempty"`
	FileCount   *int    `json:"file_count,omitempty"`
	Format      *string `json:"format,omitempty"`
	Description *string `json:"description,omitempty"`
}

// ReportDatasetsRequest is the payload for reporting datasets.
type ReportDatasetsRequest struct {
	Datasets []DatasetInfo `json:"datasets"`
}

// ReportDatasets reports scanned datasets to the master.
func (c *MasterClient) ReportDatasets(ctx context.Context, datasets []DatasetInfo) error {
	if len(datasets) == 0 {
		return nil
	}

	req := ReportDatasetsRequest{Datasets: datasets}
	return c.doRequest(ctx, "POST", "/api/v1/datasets/batch", req, nil, true)
}

// ProjectStatusUpdate represents a project status update request.
type ProjectStatusUpdate struct {
	Status    string `json:"status"`
	Message   string `json:"message,omitempty"`
	LocalPath string `json:"local_path,omitempty"`
}

// UpdateProjectStatus updates a project's status on the master.
func (c *MasterClient) UpdateProjectStatus(ctx context.Context, projectID int64, status, message, localPath string) error {
	req := ProjectStatusUpdate{
		Status:    status,
		Message:   message,
		LocalPath: localPath,
	}
	path := fmt.Sprintf("/api/v1/internal/projects/%d/status", projectID)
	return c.doRequest(ctx, "POST", path, req, nil, true)
}

// doRequest performs an HTTP request.
func (c *MasterClient) doRequest(ctx context.Context, method, path string, body any, result any, useToken bool) error {
	url := c.cfg.MasterURL + path

	var bodyReader io.Reader
	if body != nil {
		jsonData, err := json.Marshal(body)
		if err != nil {
			return fmt.Errorf("failed to marshal request: %w", err)
		}
		bodyReader = bytes.NewReader(jsonData)
	}

	req, err := http.NewRequestWithContext(ctx, method, url, bodyReader)
	if err != nil {
		return fmt.Errorf("failed to create request: %w", err)
	}

	req.Header.Set("Content-Type", "application/json")
	if useToken && c.token != "" {
		req.Header.Set("X-Agent-Token", c.token)
	}

	resp, err := c.httpClient.Do(req)
	if err != nil {
		return fmt.Errorf("request failed: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode == http.StatusUnauthorized {
		return fmt.Errorf("unauthorized: token invalid")
	}

	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		bodyBytes, _ := io.ReadAll(resp.Body)
		return fmt.Errorf("request failed with status %d: %s", resp.StatusCode, string(bodyBytes))
	}

	if result != nil {
		if err := json.NewDecoder(resp.Body).Decode(result); err != nil {
			return fmt.Errorf("failed to decode response: %w", err)
		}
	}

	return nil
}
