# OPC UA MODBUS PLC Emulator
# Makefile for easy management

.PHONY: help build up down logs scan status clean test restart monitor server-logs scanner-logs

# Default target
help:
	@echo "OPC UA MODBUS PLC Emulator"
	@echo "========================="
	@echo "Available commands:"
	@echo "  make build    - Build all Docker images"
	@echo "  make up       - Start all services"
	@echo "  make down     - Stop all services"
	@echo "  make logs     - Show logs for all services"
	@echo "  make scan     - Run a one-time scan"
	@echo "  make status   - Check service status"
	@echo "  make clean    - Clean up containers and volumes"
	@echo "  make test     - Run connection test"
	@echo "  make restart  - Restart all services"

# Build Docker images
build:
	@echo "Building Docker images..."
	docker-compose build

# Start services
up:
       @echo "Starting OPC UA services..."
       docker-compose up -d opcua-server opcua-scanner
       @echo "Waiting for server to start..."
       sleep 5
       @echo "Services started. You can now run 'make monitor' to watch values."

# Stop services
down:
	@echo "Stopping OPC UA services..."
	docker-compose down

# Show logs
logs:
	@echo "Showing logs (Ctrl+C to exit)..."
	docker-compose logs -f

# Run scanner once
scan:
	@echo "Running OPC UA scanner..."
	docker-compose run --rm opcua-scanner

# Check status
status:
	@echo "Service status:"
	docker-compose ps

# Clean up
clean:
	@echo "Cleaning up..."
	docker-compose down -v
	docker-compose rm -f
	docker system prune -f

# Connection test
test:
	@echo "Testing OPC UA connection..."
	docker-compose exec opcua-server python -c "import socket; s=socket.socket(); s.connect(('localhost', 4840)); s.close(); print('Server is responsive')"

# Restart services
restart:
	@echo "Restarting services..."
	docker-compose restart

# Monitor continuously
monitor:
	@echo "Starting continuous monitoring (Ctrl+C to stop)..."
	docker-compose run --rm opcua-scanner python opcua_scanner.py

# Server logs only
server-logs:
	@echo "Showing server logs..."
	docker-compose logs -f opcua-server

# Scanner logs only
scanner-logs:
	@echo "Showing scanner logs..."
	docker-compose logs -f opcua-scanner
