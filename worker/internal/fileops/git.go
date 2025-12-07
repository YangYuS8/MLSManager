// Package fileops provides Git operations for the worker agent.
package fileops

import (
	"context"
	"fmt"
	"os/exec"
	"strings"
	"time"
)

// CloneOptions contains options for cloning a repository.
type CloneOptions struct {
	URL        string
	Branch     string
	TargetPath string
	Depth      int // 0 means full clone
	Timeout    time.Duration
}

// CloneResult contains the result of a clone operation.
type CloneResult struct {
	Success   bool   `json:"success"`
	LocalPath string `json:"local_path,omitempty"`
	Message   string `json:"message,omitempty"`
	Error     string `json:"error,omitempty"`
}

// Clone clones a Git repository to the target path.
func Clone(ctx context.Context, opts CloneOptions) *CloneResult {
	if opts.Timeout == 0 {
		opts.Timeout = 10 * time.Minute
	}

	ctx, cancel := context.WithTimeout(ctx, opts.Timeout)
	defer cancel()

	// Build git clone command
	args := []string{"clone", "--progress"}

	if opts.Branch != "" {
		args = append(args, "--branch", opts.Branch)
	}

	if opts.Depth > 0 {
		args = append(args, "--depth", fmt.Sprintf("%d", opts.Depth))
	}

	args = append(args, opts.URL, opts.TargetPath)

	cmd := exec.CommandContext(ctx, "git", args...)
	output, err := cmd.CombinedOutput()

	if err != nil {
		return &CloneResult{
			Success: false,
			Error:   err.Error(),
			Message: string(output),
		}
	}

	return &CloneResult{
		Success:   true,
		LocalPath: opts.TargetPath,
		Message:   "Clone completed successfully",
	}
}

// PullOptions contains options for pulling a repository.
type PullOptions struct {
	RepoPath string
	Remote   string
	Branch   string
	Timeout  time.Duration
}

// PullResult contains the result of a pull operation.
type PullResult struct {
	Success bool   `json:"success"`
	Message string `json:"message,omitempty"`
	Error   string `json:"error,omitempty"`
}

// Pull pulls the latest changes from a remote repository.
func Pull(ctx context.Context, opts PullOptions) *PullResult {
	if opts.Timeout == 0 {
		opts.Timeout = 5 * time.Minute
	}
	if opts.Remote == "" {
		opts.Remote = "origin"
	}

	ctx, cancel := context.WithTimeout(ctx, opts.Timeout)
	defer cancel()

	// Build git pull command
	args := []string{"pull", opts.Remote}
	if opts.Branch != "" {
		args = append(args, opts.Branch)
	}

	cmd := exec.CommandContext(ctx, "git", args...)
	cmd.Dir = opts.RepoPath
	output, err := cmd.CombinedOutput()

	if err != nil {
		return &PullResult{
			Success: false,
			Error:   err.Error(),
			Message: string(output),
		}
	}

	return &PullResult{
		Success: true,
		Message: strings.TrimSpace(string(output)),
	}
}

// GitStatus represents the status of a Git repository.
type GitStatus struct {
	Branch        string   `json:"branch"`
	Clean         bool     `json:"clean"`
	Ahead         int      `json:"ahead"`
	Behind        int      `json:"behind"`
	Modified      []string `json:"modified,omitempty"`
	Untracked     []string `json:"untracked,omitempty"`
	LastCommit    string   `json:"last_commit,omitempty"`
	LastCommitMsg string   `json:"last_commit_msg,omitempty"`
}

// GetStatus returns the Git status of a repository.
func GetStatus(ctx context.Context, repoPath string) (*GitStatus, error) {
	status := &GitStatus{}

	// Get current branch
	branchCmd := exec.CommandContext(ctx, "git", "branch", "--show-current")
	branchCmd.Dir = repoPath
	branchOutput, err := branchCmd.Output()
	if err != nil {
		return nil, fmt.Errorf("failed to get branch: %w", err)
	}
	status.Branch = strings.TrimSpace(string(branchOutput))

	// Get status
	statusCmd := exec.CommandContext(ctx, "git", "status", "--porcelain")
	statusCmd.Dir = repoPath
	statusOutput, err := statusCmd.Output()
	if err != nil {
		return nil, fmt.Errorf("failed to get status: %w", err)
	}

	lines := strings.Split(strings.TrimSpace(string(statusOutput)), "\n")
	status.Clean = len(lines) == 1 && lines[0] == ""

	for _, line := range lines {
		if len(line) < 3 {
			continue
		}
		indicator := line[:2]
		file := strings.TrimSpace(line[3:])

		if strings.Contains(indicator, "?") {
			status.Untracked = append(status.Untracked, file)
		} else {
			status.Modified = append(status.Modified, file)
		}
	}

	// Get last commit
	logCmd := exec.CommandContext(ctx, "git", "log", "-1", "--format=%H|%s")
	logCmd.Dir = repoPath
	logOutput, err := logCmd.Output()
	if err == nil {
		parts := strings.SplitN(strings.TrimSpace(string(logOutput)), "|", 2)
		if len(parts) == 2 {
			status.LastCommit = parts[0][:8] // Short hash
			status.LastCommitMsg = parts[1]
		}
	}

	return status, nil
}

// IsGitRepo checks if a directory is a Git repository.
func IsGitRepo(path string) bool {
	cmd := exec.Command("git", "rev-parse", "--git-dir")
	cmd.Dir = path
	err := cmd.Run()
	return err == nil
}
