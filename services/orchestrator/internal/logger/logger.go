package logger

import (
	"os"

	"go.uber.org/zap"
	"go.uber.org/zap/zapcore"
)

type Logger struct {
	*zap.SugaredLogger
}

func NewLogger() *Logger {
	// Determine log level
	logLevel := zapcore.InfoLevel
	if level := os.Getenv("LOG_LEVEL"); level != "" {
		switch level {
		case "debug":
			logLevel = zapcore.DebugLevel
		case "warn":
			logLevel = zapcore.WarnLevel
		case "error":
			logLevel = zapcore.ErrorLevel
		}
	}

	// Configure encoder
	encoderConfig := zapcore.EncoderConfig{
		TimeKey:        "timestamp",
		LevelKey:       "level",
		NameKey:        "logger",
		CallerKey:      "caller",
		MessageKey:     "message",
		StacktraceKey:  "stacktrace",
		LineEnding:     zapcore.DefaultLineEnding,
		EncodeLevel:    zapcore.LowercaseLevelEncoder,
		EncodeTime:     zapcore.ISO8601TimeEncoder,
		EncodeDuration: zapcore.SecondsDurationEncoder,
		EncodeCaller:   zapcore.ShortCallerEncoder,
	}

	// Create core
	core := zapcore.NewCore(
		zapcore.NewJSONEncoder(encoderConfig),
		zapcore.AddSync(os.Stdout),
		logLevel,
	)

	// Create logger
	logger := zap.New(core, zap.AddCaller(), zap.AddStacktrace(zapcore.ErrorLevel))
	
	return &Logger{SugaredLogger: logger.Sugar()}
}
