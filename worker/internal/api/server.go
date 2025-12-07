// Package api provides HTTP API server for the worker agent.
package api

import (
	"context"
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"strconv"
	"strings"
	"time"

	"github.com/YangYuS8/mlsmanager-worker/internal/client"
	"github.com/YangYuS8/mlsmanager-worker/internal/config"
	"github.com/YangYuS8/mlsmanager-worker/internal/fileops"
)

// Server represents the HTTP API server.
type Server struct {
	config       *config.Config
	masterClient *client.MasterClient
	httpServer   *http.Server
	mux          *http.ServeMux
}

// NewServer creates a new HTTP API server.
func NewServer(cfg *config.Config, mc *client.MasterClient) *Server {
	s := &Server{
		config:       cfg,
		masterClient: mc,
		mux:          http.NewServeMux(),
	}
	s.setupRoutes()
	return s
}

// setupRoutes configures all API routes.
func (s *Server) setupRoutes() {
	// Health check (no auth required)
	s.mux.HandleFunc("/health", s.handleHealth)

	// API routes (with auth)
	s.mux.HandleFunc("/api/v1/projects/clone", s.authMiddleware(s.handleCloneProject))
	s.mux.HandleFunc("/api/v1/projects/", s.authMiddleware(s.handleProjectRoutes))
}

// authMiddleware validates the X-Agent-Token header.
func (s *Server) authMiddleware(next http.HandlerFunc) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		token := r.Header.Get("X-Agent-Token")
		expectedToken := s.config.LoadToken()

		if token == "" || token != expectedToken {
			s.jsonError(w, http.StatusUnauthorized, "unauthorized")
			return
		}

		next(w, r)
	}
}

// handleHealth handles health check requests.
func (s *Server) handleHealth(w http.ResponseWriter, r *http.Request) {
	s.jsonResponse(w, http.StatusOK, map[string]interface{}{
		"status":    "healthy",
		"node_name": s.config.NodeName,
		"timestamp": time.Now().Unix(),
	})
}

// CloneRequest represents a project clone request.
type CloneRequest struct {
	ProjectID  int64  `json:"project_id"`
	GitURL     string `json:"git_url"`
	Branch     string `json:"branch"`
	TargetPath string `json:"target_path"`
}

// CloneResponse represents a project clone response.
type CloneResponse struct {
	ProjectID int64  `json:"project_id"`
	Success   bool   `json:"success"`
	Message   string `json:"message,omitempty"`
	LocalPath string `json:"local_path,omitempty"`
}

// handleCloneProject handles POST /api/v1/projects/clone
func (s *Server) handleCloneProject(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		s.jsonError(w, http.StatusMethodNotAllowed, "method not allowed")
		return
	}

	var req CloneRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		s.jsonError(w, http.StatusBadRequest, "invalid request body")
		return
	}

	// Validate required fields
	if req.GitURL == "" || req.TargetPath == "" {
		s.jsonError(w, http.StatusBadRequest, "git_url and target_path are required")
		return
	}

	// Validate and build full path
	fullPath, err := fileops.ValidatePath(s.config.ProjectsPath, req.TargetPath)
	if err != nil {
		s.jsonError(w, http.StatusBadRequest, err.Error())
		return
	}

	// Check if path already exists
	if fileops.PathExists(fullPath) {
		s.jsonError(w, http.StatusConflict, "target path already exists")
		return
	}

	// Start async clone operation
	go s.doClone(req, fullPath)

	// Return accepted response
	s.jsonResponse(w, http.StatusAccepted, CloneResponse{
		ProjectID: req.ProjectID,
		Success:   true,
		Message:   "Clone started",
		LocalPath: fullPath,
	})
}

// doClone performs the actual git clone operation asynchronously.
func (s *Server) doClone(req CloneRequest, fullPath string) {
	ctx := context.Background()

	log.Printf("[INFO] Starting clone: %s -> %s", req.GitURL, fullPath)

	result := fileops.Clone(ctx, fileops.CloneOptions{
		URL:        req.GitURL,
		Branch:     req.Branch,
		TargetPath: fullPath,
		Timeout:    10 * time.Minute,
	})

	// Update master with result (status values must be lowercase to match backend enum)
	status := "active"
	message := ""
	if !result.Success {
		status = "error"
		message = result.Error
		if result.Message != "" {
			message = result.Message
		}
		log.Printf("[ERROR] Clone failed for project %d: %s", req.ProjectID, message)
	} else {
		log.Printf("[INFO] Clone completed for project %d: %s", req.ProjectID, fullPath)
	}

	// Callback to master
	if err := s.masterClient.UpdateProjectStatus(ctx, req.ProjectID, status, message, fullPath); err != nil {
		log.Printf("[ERROR] Failed to update project status: %v", err)
	}
}

// handleProjectRoutes handles /api/v1/projects/{id}/... routes
func (s *Server) handleProjectRoutes(w http.ResponseWriter, r *http.Request) {
	// Parse path: /api/v1/projects/{id}/{action}
	path := strings.TrimPrefix(r.URL.Path, "/api/v1/projects/")
	parts := strings.Split(path, "/")

	if len(parts) < 1 || parts[0] == "" {
		s.jsonError(w, http.StatusBadRequest, "project id required")
		return
	}

	projectID, err := strconv.ParseInt(parts[0], 10, 64)
	if err != nil {
		s.jsonError(w, http.StatusBadRequest, "invalid project id")
		return
	}

	action := ""
	if len(parts) > 1 {
		action = parts[1]
	}

	switch {
	case r.Method == http.MethodPost && action == "pull":
		s.handlePullProject(w, r, projectID)
	case r.Method == http.MethodGet && action == "status":
		s.handleGetProjectStatus(w, r, projectID)
	case r.Method == http.MethodDelete && action == "":
		s.handleDeleteProject(w, r, projectID)
	default:
		s.jsonError(w, http.StatusNotFound, "not found")
	}
}

// PullRequest represents a project pull request.
type PullRequest struct {
	ProjectPath string `json:"project_path"`
	Branch      string `json:"branch"`
}

// handlePullProject handles POST /api/v1/projects/{id}/pull
func (s *Server) handlePullProject(w http.ResponseWriter, r *http.Request, projectID int64) {
	var req PullRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		s.jsonError(w, http.StatusBadRequest, "invalid request body")
		return
	}

	// Validate path
	fullPath, err := fileops.ValidatePath(s.config.ProjectsPath, req.ProjectPath)
	if err != nil {
		s.jsonError(w, http.StatusBadRequest, err.Error())
		return
	}

	// Check if it's a git repo
	if !fileops.IsGitRepo(fullPath) {
		s.jsonError(w, http.StatusBadRequest, "not a git repository")
		return
	}

	// Pull
	result := fileops.Pull(context.Background(), fileops.PullOptions{
		RepoPath: fullPath,
		Branch:   req.Branch,
	})

	s.jsonResponse(w, http.StatusOK, result)
}

// StatusRequest represents a project status request.
type StatusRequest struct {
	ProjectPath string `json:"project_path"`
}

// handleGetProjectStatus handles GET /api/v1/projects/{id}/status
func (s *Server) handleGetProjectStatus(w http.ResponseWriter, r *http.Request, projectID int64) {
	projectPath := r.URL.Query().Get("project_path")
	if projectPath == "" {
		s.jsonError(w, http.StatusBadRequest, "project_path query parameter required")
		return
	}

	// Validate path
	fullPath, err := fileops.ValidatePath(s.config.ProjectsPath, projectPath)
	if err != nil {
		s.jsonError(w, http.StatusBadRequest, err.Error())
		return
	}

	// Check if path exists
	if !fileops.PathExists(fullPath) {
		s.jsonError(w, http.StatusNotFound, "project path not found")
		return
	}

	// Get git status if it's a repo
	if fileops.IsGitRepo(fullPath) {
		status, err := fileops.GetStatus(context.Background(), fullPath)
		if err != nil {
			s.jsonError(w, http.StatusInternalServerError, err.Error())
			return
		}
		s.jsonResponse(w, http.StatusOK, status)
		return
	}

	// Return basic path info
	info, err := fileops.GetInfo(fullPath)
	if err != nil {
		s.jsonError(w, http.StatusInternalServerError, err.Error())
		return
	}
	s.jsonResponse(w, http.StatusOK, info)
}

// DeleteRequest represents a project delete request.
type DeleteRequest struct {
	ProjectPath string `json:"project_path"`
}

// handleDeleteProject handles DELETE /api/v1/projects/{id}
func (s *Server) handleDeleteProject(w http.ResponseWriter, r *http.Request, projectID int64) {
	var req DeleteRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		s.jsonError(w, http.StatusBadRequest, "invalid request body")
		return
	}

	// Validate path
	fullPath, err := fileops.ValidatePath(s.config.ProjectsPath, req.ProjectPath)
	if err != nil {
		s.jsonError(w, http.StatusBadRequest, err.Error())
		return
	}

	// Check if path exists
	if !fileops.PathExists(fullPath) {
		// Already deleted, return success
		s.jsonResponse(w, http.StatusOK, map[string]interface{}{
			"success": true,
			"message": "path already deleted",
		})
		return
	}

	// Delete
	if err := fileops.RemoveAll(fullPath); err != nil {
		s.jsonError(w, http.StatusInternalServerError, err.Error())
		return
	}

	log.Printf("[INFO] Deleted project %d path: %s", projectID, fullPath)

	s.jsonResponse(w, http.StatusOK, map[string]interface{}{
		"success": true,
		"message": "deleted successfully",
	})
}

// jsonResponse sends a JSON response.
func (s *Server) jsonResponse(w http.ResponseWriter, status int, data interface{}) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(status)
	json.NewEncoder(w).Encode(data)
}

// jsonError sends a JSON error response.
func (s *Server) jsonError(w http.ResponseWriter, status int, message string) {
	s.jsonResponse(w, status, map[string]string{"error": message})
}

// Start starts the HTTP server.
func (s *Server) Start(addr string) error {
	s.httpServer = &http.Server{
		Addr:         addr,
		Handler:      s.mux,
		ReadTimeout:  30 * time.Second,
		WriteTimeout: 30 * time.Second,
	}

	log.Printf("[INFO] Starting API server on %s", addr)
	return s.httpServer.ListenAndServe()
}

// Shutdown gracefully shuts down the HTTP server.
func (s *Server) Shutdown(ctx context.Context) error {
	if s.httpServer != nil {
		return s.httpServer.Shutdown(ctx)
	}
	return nil
}

// Addr returns the server address.
func (s *Server) Addr() string {
	return fmt.Sprintf(":%d", s.config.APIPort)
}
