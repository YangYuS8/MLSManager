# Build stage
FROM golang:1.25-alpine AS builder

WORKDIR /app

# Install build dependencies
RUN apk add --no-cache git ca-certificates

# Copy go mod files
COPY go.mod go.sum ./

# Download dependencies
RUN go mod download

# Copy source code
COPY . .

# Build the binary
RUN CGO_ENABLED=0 GOOS=linux go build -ldflags="-w -s" -o /agent ./cmd/agent

# Runtime stage
FROM alpine:3.21

RUN apk add --no-cache ca-certificates bash docker-cli

WORKDIR /app

COPY --from=builder /agent /app/agent

RUN mkdir -p /data /etc/ml-agent

# Environment variables are loaded from .env via docker-compose
# Only set minimal required defaults here
ENV AGENT_STORAGE_PATH=/data

ENTRYPOINT ["/app/agent"]
