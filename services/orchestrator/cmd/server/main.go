package main

import (
	"context"
	"log"
	"net/http"
	"os"
	"os/signal"
	"syscall"
	"time"

	"github.com/gin-gonic/gin"
	"github.com/go-redis/redis/v8"

	"optiinfra/services/orchestrator/internal/registry"
	"optiinfra/services/orchestrator/internal/task"
)

func main() {
	// Initialize Redis
	redisClient := redis.NewClient(&redis.Options{
		Addr:     getEnv("REDIS_ADDR", "localhost:6379"),
		Password: getEnv("REDIS_PASSWORD", ""),
		DB:       0,
	})

	// Test Redis connection
	ctx := context.Background()
	if err := redisClient.Ping(ctx).Err(); err != nil {
		log.Fatal("Failed to connect to Redis:", err)
	}
	log.Println("Connected to Redis")

	// Initialize Agent Registry
	agentRegistry := registry.NewRegistry(redisClient)
	agentRegistry.Start()
	defer agentRegistry.Stop()

	// Initialize Task Router
	taskRouter := task.NewRouter(redisClient, agentRegistry)
	log.Println("Task router initialized")

	// Initialize Gin
	router := gin.Default()

	// Health check endpoint
	router.GET("/health", func(c *gin.Context) {
		c.JSON(200, gin.H{
			"status":    "healthy",
			"service":   "orchestrator",
			"timestamp": time.Now(),
		})
	})

	// Register routes
	registryHandler := registry.NewHandler(agentRegistry)
	registryHandler.RegisterRoutes(router)

	taskHandler := task.NewHandler(taskRouter)
	taskHandler.RegisterRoutes(router)

	// Start server
	port := getEnv("PORT", "8080")
	log.Printf("Starting orchestrator on port %s", port)

	// Graceful shutdown
	srv := &http.Server{
		Addr:    ":" + port,
		Handler: router,
	}

	go func() {
		if err := srv.ListenAndServe(); err != nil && err != http.ErrServerClosed {
			log.Fatalf("Server failed: %v", err)
		}
	}()

	// Wait for interrupt signal
	quit := make(chan os.Signal, 1)
	signal.Notify(quit, syscall.SIGINT, syscall.SIGTERM)
	<-quit

	log.Println("Shutting down server...")

	// Graceful shutdown with timeout
	shutdownCtx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()

	if err := srv.Shutdown(shutdownCtx); err != nil {
		log.Fatal("Server forced to shutdown:", err)
	}

	log.Println("Server exited")
}

func getEnv(key, defaultValue string) string {
	if value := os.Getenv(key); value != "" {
		return value
	}
	return defaultValue
}
