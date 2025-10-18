package main

import (
	"context"
	"fmt"
	"net/http"
	"os"
	"os/signal"
	"syscall"
	"time"

	"github.com/gin-gonic/gin"
	"github.com/optiinfra/orchestrator/internal/config"
	"github.com/optiinfra/orchestrator/internal/handlers"
	"github.com/optiinfra/orchestrator/internal/logger"
)

func main() {
	// Initialize logger
	log := logger.NewLogger()
	defer log.Sync()

	log.Info("Starting OptiInfra Orchestrator")

	// Load configuration
	cfg, err := config.Load()
	if err != nil {
		log.Fatal("Failed to load configuration", "error", err)
	}

	// Set Gin mode
	if cfg.Environment == "production" {
		gin.SetMode(gin.ReleaseMode)
	}

	// Create router
	router := gin.New()
	router.Use(gin.Recovery())
	
	// Use custom logger middleware
	router.Use(func(c *gin.Context) {
		start := time.Now()
		path := c.Request.URL.Path
		c.Next()
		
		log.Info("HTTP request",
			"method", c.Request.Method,
			"path", path,
			"status", c.Writer.Status(),
			"duration_ms", time.Since(start).Milliseconds(),
		)
	})

	// Register routes
	router.GET("/health", handlers.HealthCheck)
	router.GET("/", func(c *gin.Context) {
		c.JSON(http.StatusOK, gin.H{
			"service": "OptiInfra Orchestrator",
			"version": "0.1.0",
			"status": "running",
		})
	})

	// Create server
	srv := &http.Server{
		Addr:    fmt.Sprintf(":%d", cfg.Port),
		Handler: router,
	}

	// Start server in goroutine
	go func() {
		log.Info("Server starting", "port", cfg.Port)
		if err := srv.ListenAndServe(); err != nil && err != http.ErrServerClosed {
			log.Fatal("Server failed to start", "error", err)
		}
	}()

	// Wait for interrupt signal
	quit := make(chan os.Signal, 1)
	signal.Notify(quit, syscall.SIGINT, syscall.SIGTERM)
	<-quit

	log.Info("Shutting down server...")

	// Graceful shutdown
	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()

	if err := srv.Shutdown(ctx); err != nil {
		log.Error("Server forced to shutdown", "error", err)
	}

	log.Info("Server stopped")
}
