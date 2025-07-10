# OPC UA MODBUS PLC Emulator

A complete OPC UA server emulator that simulates a MODBUS PLC connection, along with a scanner client for testing and monitoring. Built with Python using the `asyncua` library and fully containerized with Docker.

## Features

### OPC UA Server (PLC Emulator)
- **Temperature Sensors**: 10 sensors with realistic temperature variations (20-40°C)
- **Pressure Sensors**: 10 sensors with pressure readings (1000-2000 units)
- **Flow Meters**: 10 flow meters with flow rate data (20-80 L/min)
- **Motor Controls**: 10 digital motor on/off controls
- **Discrete Inputs**: 20 limit switches and digital inputs
- **Setpoints**: 10 configurable setpoint values
- **System Status**: PLC running status, communication health, error counters
- **OPC UA Methods**: Remote PLC restart functionality

### OPC UA Scanner/Client
- **Full Node Discovery**: Automatically discovers all server nodes
- **Real-time Monitoring**: Continuous monitoring of selected variables
- **Method Invocation**: Can call server methods remotely
- **Structured Output**: Organizes discovered nodes by type
- **JSON Export**: Saves scan results for analysis

## Quick Start

### Prerequisites
- Docker and Docker Compose
- Make (optional, for convenience commands)

### 1. Clone and Setup
```bash
# Create project directory
mkdir opcua-modbus-emulator
cd opcua-modbus-emulator

# Create all the files (copy the code from the artifacts above)
# Files needed:
# - opcua_server.py
# - opcua_scanner.py
# - docker-compose.yml
# - Dockerfile.server
# - Dockerfile.scanner
# - requirements.txt
# - Makefile (optional)
```

### 2. Build and Start
```bash
# Using Make (recommended)
make build
make up

# Or using Docker Compose directly
docker-compose build
docker-compose up -d opcua-server
```

### 3. Test the Scanner
```bash
# Run scanner once
make scan

# Or with Docker Compose
docker-compose run --rm opcua-scanner
```

### 4. Monitor Continuously
```bash
# Start continuous monitoring
make monitor

# Or manually
docker-compose run --rm opcua-scanner python opcua_scanner.py
```

## Usage

### Available Make Commands
```bash
make help      # Show all available commands
make build     # Build Docker images
make up        # Start the server
make down      # Stop all services
make scan      # Run scanner once
make monitor   # Start continuous monitoring
make logs      # Show logs
make status    # Check service status
make clean     # Clean up containers
make test      # Test server connectivity
make info      # Show server information
```

### Manual Docker Commands
```bash
# Start server only
docker-compose up -d opcua-server

# Run scanner interactively
docker-compose run --rm opcua-scanner

# View logs
docker-compose logs -f opcua-server
docker-compose logs -f opcua-scanner

# Stop everything
docker-compose down
```

## Server Configuration

### Connection Details
- **Server URL**: `opc.tcp://localhost:4840/freeopcua/server/`
- **Port**: 4840
- **Namespace**: `http://examples.freeopcua.github.io`

### Node Structure
```
PLC_System/
├── Temperature_Sensors/
│   ├── Temperature_Sensor_00 (Double, °C)
│   ├── Temperature_Sensor_01 (Double, °C)
│   └── ... (10 total)
├── Pressure_Sensors/
│   ├── Pressure_Sensor_00 (Double, units)
│   ├── Pressure_Sensor_01 (Double, units)
│   └── ... (10 total)
├── Flow_Meters/
│   ├── Flow_Meter_00 (Double, L/min)
│   ├── Flow_Meter_01 (Double, L/min)
│   └── ... (10 total)
├── Motor_Controls/
│   ├── Motor_00_Running (Boolean)
│   ├── Motor_01_Running (Boolean)
│   └── ... (10 total)
├── Discrete_Inputs/
│   ├── Limit_Switch_00 (Boolean)
│   ├── Limit_Switch_01 (Boolean)
│   └── ... (20 total)
├── Setpoints/
│   ├── Setpoint_00 (Double)
│   ├── Setpoint_01 (Double)
│   └── ... (10 total)
├── System_Status/
│   ├── PLC_Running (Boolean)
│   ├── Communication_OK (Boolean)
│   ├── Last_Update (DateTime)
│   └── Error_Count (UInt32)
└── Methods/
    └── RestartPLC (Method)
```

## Data Simulation

The emulator generates realistic MODBUS PLC data:

- **Temperature**: Base temperatures 20-40°C with ±2.5°C variation
- **Pressure**: Base pressures 1000-2000 units with ±25 unit variation
- **Flow**: Flow rates 20-80 L/min with realistic fluctuations
- **Motors**: Random on/off states with persistence
- **Discrete Inputs**: Occasional state changes (limit switches)
- **Communication**: Simulated 1% communication error rate

## Monitoring Output Example

```
============================================================
MONITORING UPDATE - 2024-01-15 10:30:45
============================================================
Temperature_Sensor_00: 22.35
Temperature_Sensor_01: 24.12
Pressure_Sensor_00: 1045.2
Flow_Meter_00: 67.89
Motor_00_Running: True
PLC_Running: True
Communication_OK: True
Error_Count: 2
```

## Use Cases

### Industrial Automation Testing
- Test HMI/SCADA systems
- Validate OPC UA client applications
- Simulate factory floor equipment

### Development & Training
- Learn OPC UA protocol
- Develop industrial IoT applications
- Test data acquisition systems

### Integration Testing
- Validate communication protocols
- Test system integration
- Simulate equipment failures

## Security Notes

- The emulator runs with non-root users in containers
- No authentication is configured (suitable for testing only)
- For production use, implement proper OPC UA security

## Troubleshooting

### Common Issues

1. **Port 4840 already in use**
   ```bash
   # Check what's using the port
   lsof -i :4840
   # Kill the process or change port in docker-compose.yml
   ```

2. **Scanner can't connect**
   ```bash
   # Check if server is running
   make status
   # Check server logs
   make server-logs
   ```

3. **Permission denied**
   ```bash
   # Fix permissions
   sudo chown -R $USER:$USER ./logs ./scan_results
   ```

### Logs Location
- Server logs: `./logs/`
- Scan results: `./scan_results/scan_results.json`

## Dependencies

- Python 3.11+
- asyncua 1.0.6
- cryptography 41.0.7
- Docker & Docker Compose

## License

This project is provided as-is for educational and testing purposes.

## Contributing

Feel free to submit issues and enhancement requests!