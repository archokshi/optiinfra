package handlers

import (
	"net/http"
	"time"

	"github.com/gin-gonic/gin"
)

type HealthResponse struct {
	Status    string    `json:"status"`
	Timestamp time.Time `json:"timestamp"`
	Version   string    `json:"version"`
	Uptime    string    `json:"uptime"`
}

var startTime = time.Now()

func HealthCheck(c *gin.Context) {
	uptime := time.Since(startTime)
	
	response := HealthResponse{
		Status:    "healthy",
		Timestamp: time.Now(),
		Version:   "0.1.0",
		Uptime:    uptime.String(),
	}

	c.JSON(http.StatusOK, response)
}
