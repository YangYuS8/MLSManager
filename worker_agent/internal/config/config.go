// Package config provides configuration management for the worker agent.
package config

import (
	"os"
	"path/filepath"
	"strings"

	"github.com/caarlos0/env/v11"
)

// Config holds all agent configuration settings.
type Config struct {
	// Master node connection
	MasterURL string `env:"AGENT_MASTER_URL" envDefault:"http://localhost:8000"`

	// Node identification
	NodeName     string `env:"AGENT_NODE_NAME" envDefault:"worker-001"`
	NodeHostname string `env:"AGENT_NODE_HOSTNAME"`

	// Timing (in seconds)
	HeartbeatInterval   int `env:"AGENT_HEARTBEAT_INTERVAL" envDefault:"30"`
	JobPollInterval     int `env:"AGENT_JOB_POLL_INTERVAL" envDefault:"10"`
	DatasetScanInterval int `env:"AGENT_DATASET_SCAN_INTERVAL" envDefault:"300"`

	// Paths
	StoragePath   string `env:"AGENT_STORAGE_PATH" envDefault:"/data"`
	DatasetsPath  string `env:"AGENT_DATASETS_PATH" envDefault:"/data/datasets"`
	JobsWorkspace string `env:"AGENT_JOBS_WORKSPACE" envDefault:"/data/jobs"`
	LogPath       string `env:"AGENT_LOG_PATH" envDefault:"/var/log/ml-agent"`

	// Token management
	AgentToken string `env:"AGENT_TOKEN"`
	TokenFile  string `env:"AGENT_TOKEN_FILE" envDefault:"/etc/ml-agent/token"`

	// Development mode
	DevMode bool `env:"AGENT_DEV_MODE" envDefault:"false"`
}

// Load loads configuration from environment variables.
func Load() (*Config, error) {
	cfg := &Config{}
	if err := env.Parse(cfg); err != nil {
		return nil, err
	}

	// Normalize master URL
	cfg.MasterURL = strings.TrimSuffix(cfg.MasterURL, "/")

	// Auto-detect hostname if not set
	if cfg.NodeHostname == "" {
		hostname, err := os.Hostname()
		if err == nil {
			cfg.NodeHostname = hostname
		}
	}

	return cfg, nil
}

// LoadToken loads the agent token from file or environment.
func (c *Config) LoadToken() string {
	// First check environment variable
	if c.AgentToken != "" {
		return c.AgentToken
	}

	// Then check token file
	data, err := os.ReadFile(c.TokenFile)
	if err != nil {
		return ""
	}

	return strings.TrimSpace(string(data))
}

// SaveToken saves the agent token to file.
func (c *Config) SaveToken(token string) error {
	// Create directory if not exists
	dir := filepath.Dir(c.TokenFile)
	if err := os.MkdirAll(dir, 0755); err != nil {
		return err
	}

	// Write token with restricted permissions
	if err := os.WriteFile(c.TokenFile, []byte(token), 0600); err != nil {
		return err
	}

	return nil
}
