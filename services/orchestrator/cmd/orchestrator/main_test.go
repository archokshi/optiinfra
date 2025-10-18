package main

import (
	"net/http"
	"net/http/httptest"
	"testing"

	"github.com/gin-gonic/gin"
	"github.com/optiinfra/orchestrator/internal/handlers"
)

func TestHealthCheck(t *testing.T) {
	// Setup
	gin.SetMode(gin.TestMode)
	router := gin.New()
	router.GET("/health", handlers.HealthCheck)

	// Test
	w := httptest.NewRecorder()
	req, _ := http.NewRequest("GET", "/health", nil)
	router.ServeHTTP(w, req)

	// Assert
	if w.Code != http.StatusOK {
		t.Errorf("Expected status 200, got %d", w.Code)
	}

	// Check JSON response contains "healthy"
	body := w.Body.String()
	if !contains(body, "healthy") {
		t.Errorf("Expected 'healthy' in response, got: %s", body)
	}
}

func contains(s, substr string) bool {
	return len(s) >= len(substr) && 
		(s == substr || len(s) > len(substr) && 
		(s[:len(substr)] == substr || contains(s[1:], substr)))
}
