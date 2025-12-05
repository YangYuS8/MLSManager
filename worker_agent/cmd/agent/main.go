// Package main is the entry point for the ML-Server-Manager Worker Agent.
package main

import (
	"context"
	"fmt"
	"os"
	"os/signal"
	"strings"
	"syscall"
	"time"

	"github.com/YangYuS8/mlsmanager-worker-agent/internal/client"
	"github.com/YangYuS8/mlsmanager-worker-agent/internal/config"
	"github.com/YangYuS8/mlsmanager-worker-agent/internal/executor"
	"github.com/YangYuS8/mlsmanager-worker-agent/internal/scanner"
)

func main() {
	// Load configuration
	cfg, err := config.Load()
	if err != nil {
		log("FATAL", "Failed to load configuration: %v", err)
		os.Exit(1)
	}

	// Create context with cancellation for graceful shutdown
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()

	// Handle shutdown signals
	sigChan := make(chan os.Signal, 1)
	signal.Notify(sigChan, syscall.SIGINT, syscall.SIGTERM)

	go func() {
		sig := <-sigChan
		log("INFO", "Received signal %v, shutting down...", sig)
		cancel()
	}()

	// Print startup banner
	printBanner(cfg)

	// Create master client
	masterClient := client.NewMasterClient(cfg)

	// Register with master if no token
	if masterClient.Token() == "" {
		log("INFO", "No token found, registering with master...")
		if err := registerWithRetry(ctx, masterClient, 5); err != nil {
			log("FATAL", "Failed to register: %v", err)
			os.Exit(1)
		}
	}

	// Create executor and scanner
	exec := executor.NewExecutor(cfg, masterClient)
	scan := scanner.NewScanner()

	// Start main loop
	if err := runMainLoop(ctx, cfg, masterClient, exec, scan); err != nil {
		if err != context.Canceled {
			log("ERROR", "Main loop error: %v", err)
		}
	}

	// Cleanup
	log("INFO", "Cancelling running jobs...")
	exec.CancelAll()

	log("INFO", "Agent stopped gracefully")
}

// printBanner prints the startup banner.
func printBanner(cfg *config.Config) {
	log("INFO", strings.Repeat("=", 60))
	log("INFO", "Starting ML-Server-Manager Worker Agent (Go)")
	log("INFO", "Version: 1.0.0")
	log("INFO", strings.Repeat("-", 60))
	log("INFO", "Node Name:    %s", cfg.NodeName)
	log("INFO", "Hostname:     %s", cfg.NodeHostname)
	log("INFO", "Master URL:   %s", cfg.MasterURL)
	log("INFO", "Storage Path: %s", cfg.StoragePath)
	log("INFO", "Dev Mode:     %v", cfg.DevMode)
	log("INFO", strings.Repeat("=", 60))
}

// registerWithRetry attempts to register with the master with retries.
func registerWithRetry(ctx context.Context, client *client.MasterClient, maxAttempts int) error {
	for attempt := 1; attempt <= maxAttempts; attempt++ {
		select {
		case <-ctx.Done():
			return ctx.Err()
		default:
		}

		err := client.Register(ctx)
		if err == nil {
			log("INFO", "Registered successfully. Node ID: %s", client.NodeID())
			return nil
		}

		log("WARN", "Registration attempt %d/%d failed: %v", attempt, maxAttempts, err)

		if attempt < maxAttempts {
			time.Sleep(5 * time.Second)
		}
	}

	return fmt.Errorf("failed to register after %d attempts", maxAttempts)
}

// runMainLoop runs the main agent loop.
func runMainLoop(
	ctx context.Context,
	cfg *config.Config,
	masterClient *client.MasterClient,
	exec *executor.Executor,
	scan *scanner.Scanner,
) error {
	heartbeatTicker := time.NewTicker(time.Duration(cfg.HeartbeatInterval) * time.Second)
	defer heartbeatTicker.Stop()

	jobPollTicker := time.NewTicker(time.Duration(cfg.JobPollInterval) * time.Second)
	defer jobPollTicker.Stop()

	datasetScanTicker := time.NewTicker(time.Duration(cfg.DatasetScanInterval) * time.Second)
	defer datasetScanTicker.Stop()

	// Initial heartbeat
	sendHeartbeat(ctx, masterClient)

	// Initial dataset scan
	scanDatasets(ctx, cfg, masterClient, scan)

	log("INFO", "Agent started, entering main loop...")

	for {
		select {
		case <-ctx.Done():
			return ctx.Err()

		case <-heartbeatTicker.C:
			sendHeartbeat(ctx, masterClient)

		case <-jobPollTicker.C:
			processJobs(ctx, masterClient, exec)

		case <-datasetScanTicker.C:
			scanDatasets(ctx, cfg, masterClient, scan)
		}
	}
}

// sendHeartbeat sends a heartbeat to the master.
func sendHeartbeat(ctx context.Context, masterClient *client.MasterClient) {
	if err := masterClient.Heartbeat(ctx); err != nil {
		log("ERROR", "Heartbeat failed: %v", err)

		// Try to re-register if unauthorized
		if strings.Contains(err.Error(), "unauthorized") {
			log("WARN", "Token invalid, attempting re-registration...")
			if regErr := masterClient.Register(ctx); regErr != nil {
				log("ERROR", "Re-registration failed: %v", regErr)
			}
		}
	} else {
		log("INFO", "Heartbeat sent")
	}
}

// processJobs fetches and executes pending jobs.
func processJobs(ctx context.Context, masterClient *client.MasterClient, exec *executor.Executor) {
	jobs, err := masterClient.FetchPendingJobs(ctx)
	if err != nil {
		log("ERROR", "Failed to fetch jobs: %v", err)
		return
	}

	for _, job := range jobs {
		select {
		case <-ctx.Done():
			return
		default:
		}

		log("INFO", "Executing job %d: %s", job.ID, job.Name)

		result := exec.Execute(ctx, job)

		if result.ExitCode == 0 {
			exitCode := 0
			if err := masterClient.UpdateJobStatus(ctx, job.ID, "completed", &exitCode, nil); err != nil {
				log("ERROR", "Failed to update job status: %v", err)
			}
			log("INFO", "Job %d completed successfully", job.ID)
		} else {
			if err := masterClient.UpdateJobStatus(ctx, job.ID, "failed", &result.ExitCode, &result.ErrorMessage); err != nil {
				log("ERROR", "Failed to update job status: %v", err)
			}
			log("ERROR", "Job %d failed: %s", job.ID, result.ErrorMessage)
		}
	}
}

// scanDatasets scans and reports datasets to the master.
func scanDatasets(ctx context.Context, cfg *config.Config, masterClient *client.MasterClient, scan *scanner.Scanner) {
	log("INFO", "Scanning datasets...")

	datasets := scan.Scan(cfg.DatasetsPath)
	if len(datasets) == 0 {
		log("INFO", "No datasets found")
		return
	}

	if err := masterClient.ReportDatasets(ctx, datasets); err != nil {
		log("ERROR", "Failed to report datasets: %v", err)
	} else {
		log("INFO", "Reported %d datasets", len(datasets))
	}
}

// log prints a formatted log message.
func log(level, format string, args ...any) {
	timestamp := time.Now().Format(time.RFC3339)
	message := fmt.Sprintf(format, args...)
	fmt.Printf("[%s] [%s] %s\n", timestamp, level, message)
}
