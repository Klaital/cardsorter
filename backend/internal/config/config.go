package config

import (
	"fmt"
	"github.com/caarlos0/env/v11"
	"log/slog"
	"os"
	"strings"
)

type Config struct {
	LogLevelStr string `env:"LOG_LEVEL" envDefault:"INFO"`
	LogLevel    slog.Level

	DB struct {
		Name     string `env:"DB_NAME" envDefault:"gilgamesh_test"`
		User     string `env:"DB_USER,required"`
		Password string `env:"DB_PASS,required"`
		Port     string `env:"DB_PORT" envDefault:"3306"`
		Host     string `env:"DB_HOST" envDefault:"localhost"`
	}

	HttpPort string `env:"HTTP_PORT" envDefault:":8080"`
	GrpcPort string `env:"GRPC_PORT" envDefault:":9090"`

	JwtKeyStr string `env:"JWT_KEY"`
	JwtKey    []byte
}

func ParseEnv() Config {
	// TODO: return a singleton config
	cfg, err := env.ParseAs[Config]()
	if err != nil {
		slog.Error("Failed to parse environment", "err", err.Error())
		os.Exit(1)
	}
	cfg.LogLevel = getLogLevelFromStr(cfg.LogLevelStr)
	slog.SetLogLoggerLevel(cfg.LogLevel)
	cfg.JwtKey = []byte(cfg.JwtKeyStr)
	return cfg
}

func (c Config) MysqlDbString() string {
	return fmt.Sprintf("%s:%s@tcp(%s:%s)/%s?parseTime=true", c.DB.User, c.DB.Password, c.DB.Host, c.DB.Port, c.DB.Name)
}

func (c Config) MysqlDbStringRedacted() string {
	return fmt.Sprintf("%s:%s@tcp(%s:%s)/%s?parseTime=true", c.DB.User, "***REDACTED***", c.DB.Host, c.DB.Port, c.DB.Name)
}

func getLogLevelFromStr(levelStr string) slog.Level {
	switch strings.ToUpper(levelStr) {
	case "DEBUG":
		return slog.LevelDebug
	case "INFO":
		return slog.LevelInfo
	case "WARN":
		return slog.LevelWarn
	case "ERROR":
		return slog.LevelError
	default:
		return slog.LevelInfo // Default to Info if not set or invalid
	}
}
