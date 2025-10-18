package config

import (
	"os"
	"strconv"

	"github.com/joho/godotenv"
)

type Config struct {
	Port        int
	Environment string
	LogLevel    string
}

func Load() (*Config, error) {
	// Load .env file if exists (ignore error in production)
	godotenv.Load()

	port := 8080
	if portStr := os.Getenv("ORCHESTRATOR_PORT"); portStr != "" {
		if p, err := strconv.Atoi(portStr); err == nil {
			port = p
		}
	}

	return &Config{
		Port:        port,
		Environment: getEnv("ENVIRONMENT", "development"),
		LogLevel:    getEnv("LOG_LEVEL", "info"),
	}, nil
}

func getEnv(key, defaultValue string) string {
	if value := os.Getenv(key); value != "" {
		return value
	}
	return defaultValue
}
