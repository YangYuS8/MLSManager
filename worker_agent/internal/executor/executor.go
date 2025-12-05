// Package executor provides job execution functionality.
package executor

import (
	"context"
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"sync"
	"syscall"
	"time"

	"github.com/YangYuS8/mlsmanager-worker-agent/internal/client"
	"github.com/YangYuS8/mlsmanager-worker-agent/internal/config"
)

// JobResult represents the result of a job execution.
type JobResult struct {
	ExitCode     int
	ErrorMessage string
}

// Executor executes jobs in various environments.
type Executor struct {
	cfg         *config.Config
	masterClient *client.MasterClient

	mu          sync.Mutex
	runningJobs map[int]*exec.Cmd
}

// NewExecutor creates a new job executor.
func NewExecutor(cfg *config.Config, masterClient *client.MasterClient) *Executor {
	return &Executor{
		cfg:         cfg,
		masterClient: masterClient,
		runningJobs: make(map[int]*exec.Cmd),
	}
}

// Execute runs a job and returns the result.
func (e *Executor) Execute(ctx context.Context, job client.Job) JobResult {
	// Notify master that job is running
	if err := e.masterClient.UpdateJobStatus(ctx, job.ID, "running", nil, nil); err != nil {
		fmt.Printf("[WARN] Failed to update job status to running: %v\n", err)
	}

	// Prepare working directory
	workDir := job.WorkingDirectory
	if workDir == "" {
		workDir = filepath.Join(e.cfg.JobsWorkspace, fmt.Sprintf("job_%d", job.ID))
	}
	if err := os.MkdirAll(workDir, 0755); err != nil {
		errMsg := fmt.Sprintf("failed to create work directory: %v", err)
		return JobResult{ExitCode: -1, ErrorMessage: errMsg}
	}

	// Execute based on environment
	var result JobResult
	switch job.Environment {
	case "docker":
		result = e.runDocker(ctx, job, workDir)
	case "conda":
		result = e.runConda(ctx, job, workDir)
	case "venv":
		result = e.runVenv(ctx, job, workDir)
	default:
		result = e.runSystem(ctx, job, workDir)
	}

	return result
}

// Cancel cancels a running job.
func (e *Executor) Cancel(jobID int) bool {
	e.mu.Lock()
	cmd, exists := e.runningJobs[jobID]
	e.mu.Unlock()

	if !exists || cmd.Process == nil {
		return false
	}

	// Send SIGTERM first
	if err := cmd.Process.Signal(syscall.SIGTERM); err != nil {
		// If SIGTERM fails, force kill
		cmd.Process.Kill()
	}

	// Wait for graceful shutdown
	done := make(chan struct{})
	go func() {
		cmd.Wait()
		close(done)
	}()

	select {
	case <-done:
		return true
	case <-time.After(10 * time.Second):
		cmd.Process.Kill()
		return true
	}
}

// CancelAll cancels all running jobs.
func (e *Executor) CancelAll() {
	e.mu.Lock()
	jobIDs := make([]int, 0, len(e.runningJobs))
	for id := range e.runningJobs {
		jobIDs = append(jobIDs, id)
	}
	e.mu.Unlock()

	for _, id := range jobIDs {
		e.Cancel(id)
	}
}

// runSystem executes a job directly in the system shell.
func (e *Executor) runSystem(ctx context.Context, job client.Job, workDir string) JobResult {
	timeout := time.Duration(job.TimeoutSeconds) * time.Second
	if timeout == 0 {
		timeout = time.Hour // Default 1 hour
	}

	ctx, cancel := context.WithTimeout(ctx, timeout)
	defer cancel()

	cmd := exec.CommandContext(ctx, "sh", "-c", job.Command)
	cmd.Dir = workDir
	cmd.Env = e.buildEnv(job.EnvironmentVars)

	e.mu.Lock()
	e.runningJobs[job.ID] = cmd
	e.mu.Unlock()

	defer func() {
		e.mu.Lock()
		delete(e.runningJobs, job.ID)
		e.mu.Unlock()
	}()

	output, err := cmd.CombinedOutput()
	if err != nil {
		exitCode := -1
		if exitError, ok := err.(*exec.ExitError); ok {
			exitCode = exitError.ExitCode()
		}
		errMsg := truncate(string(output), 1000)
		if errMsg == "" {
			errMsg = err.Error()
		}
		return JobResult{ExitCode: exitCode, ErrorMessage: errMsg}
	}

	return JobResult{ExitCode: 0}
}

// runDocker executes a job in a Docker container.
func (e *Executor) runDocker(ctx context.Context, job client.Job, workDir string) JobResult {
	timeout := time.Duration(job.TimeoutSeconds) * time.Second
	if timeout == 0 {
		timeout = time.Hour
	}

	ctx, cancel := context.WithTimeout(ctx, timeout)
	defer cancel()

	// Get Docker configuration
	envConfig := job.EnvConfig
	image := "python:3.12"
	if img, ok := envConfig["image"].(string); ok {
		image = img
	}

	// Build docker run command
	args := []string{"run", "--rm"}

	// Add volume mounts
	args = append(args, "-v", fmt.Sprintf("%s:/workspace", workDir))
	if volumes, ok := envConfig["volumes"].([]any); ok {
		for _, v := range volumes {
			if vol, ok := v.(string); ok {
				args = append(args, "-v", vol)
			}
		}
	}

	// Add GPU support
	if gpu, ok := envConfig["gpu"].(bool); ok && gpu {
		args = append(args, "--gpus", "all")
	}

	// Add environment variables
	for k, v := range job.EnvironmentVars {
		args = append(args, "-e", fmt.Sprintf("%s=%s", k, v))
	}

	// Set working directory and image
	args = append(args, "-w", "/workspace", image)

	// Add command
	args = append(args, "sh", "-c", job.Command)

	cmd := exec.CommandContext(ctx, "docker", args...)

	e.mu.Lock()
	e.runningJobs[job.ID] = cmd
	e.mu.Unlock()

	defer func() {
		e.mu.Lock()
		delete(e.runningJobs, job.ID)
		e.mu.Unlock()
	}()

	output, err := cmd.CombinedOutput()
	if err != nil {
		exitCode := -1
		if exitError, ok := err.(*exec.ExitError); ok {
			exitCode = exitError.ExitCode()
		}
		errMsg := truncate(string(output), 1000)
		if errMsg == "" {
			errMsg = err.Error()
		}
		return JobResult{ExitCode: exitCode, ErrorMessage: errMsg}
	}

	return JobResult{ExitCode: 0}
}

// runConda executes a job in a conda environment.
func (e *Executor) runConda(ctx context.Context, job client.Job, workDir string) JobResult {
	timeout := time.Duration(job.TimeoutSeconds) * time.Second
	if timeout == 0 {
		timeout = time.Hour
	}

	ctx, cancel := context.WithTimeout(ctx, timeout)
	defer cancel()

	// Get conda environment name
	envName := "base"
	if name, ok := job.EnvConfig["env_name"].(string); ok {
		envName = name
	}

	// Wrap command with conda activation
	wrappedCmd := fmt.Sprintf(
		"source $(conda info --base)/etc/profile.d/conda.sh && conda activate %s && %s",
		envName, job.Command,
	)

	cmd := exec.CommandContext(ctx, "bash", "-c", wrappedCmd)
	cmd.Dir = workDir
	cmd.Env = e.buildEnv(job.EnvironmentVars)

	e.mu.Lock()
	e.runningJobs[job.ID] = cmd
	e.mu.Unlock()

	defer func() {
		e.mu.Lock()
		delete(e.runningJobs, job.ID)
		e.mu.Unlock()
	}()

	output, err := cmd.CombinedOutput()
	if err != nil {
		exitCode := -1
		if exitError, ok := err.(*exec.ExitError); ok {
			exitCode = exitError.ExitCode()
		}
		errMsg := truncate(string(output), 1000)
		if errMsg == "" {
			errMsg = err.Error()
		}
		return JobResult{ExitCode: exitCode, ErrorMessage: errMsg}
	}

	return JobResult{ExitCode: 0}
}

// runVenv executes a job in a Python virtual environment.
func (e *Executor) runVenv(ctx context.Context, job client.Job, workDir string) JobResult {
	timeout := time.Duration(job.TimeoutSeconds) * time.Second
	if timeout == 0 {
		timeout = time.Hour
	}

	ctx, cancel := context.WithTimeout(ctx, timeout)
	defer cancel()

	// Get venv path
	venvPath := ".venv"
	if path, ok := job.EnvConfig["venv_path"].(string); ok {
		venvPath = path
	}

	// Resolve absolute path
	if !filepath.IsAbs(venvPath) {
		venvPath = filepath.Join(workDir, venvPath)
	}

	// Wrap command with venv activation
	activateScript := filepath.Join(venvPath, "bin", "activate")
	wrappedCmd := fmt.Sprintf("source %s && %s", activateScript, job.Command)

	cmd := exec.CommandContext(ctx, "bash", "-c", wrappedCmd)
	cmd.Dir = workDir
	cmd.Env = e.buildEnv(job.EnvironmentVars)

	e.mu.Lock()
	e.runningJobs[job.ID] = cmd
	e.mu.Unlock()

	defer func() {
		e.mu.Lock()
		delete(e.runningJobs, job.ID)
		e.mu.Unlock()
	}()

	output, err := cmd.CombinedOutput()
	if err != nil {
		exitCode := -1
		if exitError, ok := err.(*exec.ExitError); ok {
			exitCode = exitError.ExitCode()
		}
		errMsg := truncate(string(output), 1000)
		if errMsg == "" {
			errMsg = err.Error()
		}
		return JobResult{ExitCode: exitCode, ErrorMessage: errMsg}
	}

	return JobResult{ExitCode: 0}
}

// buildEnv builds environment variables for job execution.
func (e *Executor) buildEnv(envVars map[string]string) []string {
	env := os.Environ()
	for k, v := range envVars {
		env = append(env, fmt.Sprintf("%s=%s", k, v))
	}
	return env
}

// truncate truncates a string to the specified length.
func truncate(s string, maxLen int) string {
	if len(s) <= maxLen {
		return s
	}
	return s[:maxLen]
}
