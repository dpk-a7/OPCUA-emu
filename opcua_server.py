#!/usr/bin/env python3
"""
OPC UA Emulator that simulates a MODBUS PLC connection
Based on python-opcua examples
"""

import asyncio
import logging
import random
import time
from datetime import datetime
from asyncua import ua, Server
from asyncua.common.methods import uamethod

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ModbusPLCEmulator:
    """Simulates MODBUS PLC data"""
    
    def __init__(self):
        self.coils = [False] * 100  # Discrete outputs
        self.discrete_inputs = [False] * 100  # Discrete inputs
        self.holding_registers = [0] * 100  # Analog outputs
        self.input_registers = [0] * 100  # Analog inputs
        self.start_time = time.time()
        
    def update_data(self):
        """Simulate changing PLC data"""
        current_time = time.time()
        elapsed = current_time - self.start_time
        
        # Simulate temperature sensors (input registers 0-9)
        for i in range(10):
            base_temp = 20 + i * 2  # Base temperature
            variation = 5 * random.random() - 2.5  # ±2.5°C variation
            self.input_registers[i] = int((base_temp + variation) * 100)  # Scale by 100
        
        # Simulate pressure sensors (input registers 10-19)
        for i in range(10, 20):
            base_pressure = 1000 + (i-10) * 100  # Base pressure
            variation = 50 * random.random() - 25  # ±25 variation
            self.input_registers[i] = int(base_pressure + variation)
        
        # Simulate flow meters (input registers 20-29)
        for i in range(20, 30):
            flow = 50 + 30 * abs(random.random() - 0.5)  # 20-80 flow rate
            self.input_registers[i] = int(flow * 100)
        
        # Simulate motor status (coils 0-9)
        for i in range(10):
            # Random on/off with some persistence
            if random.random() < 0.1:  # 10% chance to change state
                self.coils[i] = not self.coils[i]
        
        # Simulate discrete inputs (limit switches, etc.)
        for i in range(20):
            if random.random() < 0.05:  # 5% chance to change
                self.discrete_inputs[i] = not self.discrete_inputs[i]
        
        # Simulate setpoints in holding registers
        for i in range(10):
            if random.random() < 0.02:  # 2% chance to change
                self.holding_registers[i] = random.randint(0, 1000)

class OPCUAServer:
    def __init__(self):
        self.server = None
        self.plc_emulator = ModbusPLCEmulator()
        self.nodes = {}
        
    async def init_server(self):
        """Initialize OPC UA server"""
        self.server = Server()
        await self.server.init()
        
        # Server configuration
        self.server.set_endpoint("opc.tcp://0.0.0.0:4840/freeopcua/server/")
        self.server.set_server_name("MODBUS PLC Emulator")
        
        # Setup namespace
        uri = "http://examples.freeopcua.github.io"
        idx = await self.server.register_namespace(uri)
        
        # Create object structure
        objects = self.server.get_objects_node()
        
        # PLC Root Object
        plc_object = await objects.add_object(idx, "PLC_System")
        
        # Add method for PLC control
        await plc_object.add_method(
            idx, "RestartPLC", self.restart_plc,
            [ua.VariantType.Boolean], [ua.VariantType.String]
        )
        
        # Temperature Sensors
        temp_folder = await plc_object.add_folder(idx, "Temperature_Sensors")
        self.nodes['temperatures'] = []
        for i in range(10):
            temp_node = await temp_folder.add_variable(
                idx, f"Temperature_Sensor_{i:02d}", 0.0, ua.VariantType.Double
            )
            await temp_node.set_writable()
            self.nodes['temperatures'].append(temp_node)
        
        # Pressure Sensors
        pressure_folder = await plc_object.add_folder(idx, "Pressure_Sensors")
        self.nodes['pressures'] = []
        for i in range(10):
            pressure_node = await pressure_folder.add_variable(
                idx, f"Pressure_Sensor_{i:02d}", 0.0, ua.VariantType.Double
            )
            await pressure_node.set_writable()
            self.nodes['pressures'].append(pressure_node)
        
        # Flow Meters
        flow_folder = await plc_object.add_folder(idx, "Flow_Meters")
        self.nodes['flows'] = []
        for i in range(10):
            flow_node = await flow_folder.add_variable(
                idx, f"Flow_Meter_{i:02d}", 0.0, ua.VariantType.Double
            )
            await flow_node.set_writable()
            self.nodes['flows'].append(flow_node)
        
        # Motor Controls (Coils)
        motor_folder = await plc_object.add_folder(idx, "Motor_Controls")
        self.nodes['motors'] = []
        for i in range(10):
            motor_node = await motor_folder.add_variable(
                idx, f"Motor_{i:02d}_Running", False, ua.VariantType.Boolean
            )
            await motor_node.set_writable()
            self.nodes['motors'].append(motor_node)
        
        # Discrete Inputs
        discrete_folder = await plc_object.add_folder(idx, "Discrete_Inputs")
        self.nodes['discrete'] = []
        for i in range(20):
            discrete_node = await discrete_folder.add_variable(
                idx, f"Limit_Switch_{i:02d}", False, ua.VariantType.Boolean
            )
            await discrete_node.set_writable()
            self.nodes['discrete'].append(discrete_node)
        
        # Setpoints (Holding Registers)
        setpoint_folder = await plc_object.add_folder(idx, "Setpoints")
        self.nodes['setpoints'] = []
        for i in range(10):
            setpoint_node = await setpoint_folder.add_variable(
                idx, f"Setpoint_{i:02d}", 0.0, ua.VariantType.Double
            )
            await setpoint_node.set_writable()
            self.nodes['setpoints'].append(setpoint_node)
        
        # System Status
        status_folder = await plc_object.add_folder(idx, "System_Status")
        self.nodes['status'] = {}
        
        # PLC Status
        self.nodes['status']['plc_running'] = await status_folder.add_variable(
            idx, "PLC_Running", True, ua.VariantType.Boolean
        )
        
        # Communication Status
        self.nodes['status']['comm_status'] = await status_folder.add_variable(
            idx, "Communication_OK", True, ua.VariantType.Boolean
        )
        
        # Last Update Time
        self.nodes['status']['last_update'] = await status_folder.add_variable(
            idx, "Last_Update", datetime.now(), ua.VariantType.DateTime
        )
        
        # Error Count
        self.nodes['status']['error_count'] = await status_folder.add_variable(
            idx, "Error_Count", 0, ua.VariantType.UInt32
        )
        
        logger.info("OPC UA Server initialized with MODBUS PLC emulation")
    
    @uamethod
    async def restart_plc(self, parent, force_restart):
        """Method to restart PLC simulation"""
        if force_restart:
            logger.info("PLC restart requested")
            self.plc_emulator = ModbusPLCEmulator()
            await self.nodes['status']['error_count'].write_value(0)
            return "PLC restarted successfully"
        else:
            return "PLC restart cancelled"
    
    async def update_values(self):
        """Update OPC UA values from PLC emulator"""
        try:
            # Update PLC data
            self.plc_emulator.update_data()
            
            # Update temperature values
            for i, node in enumerate(self.nodes['temperatures']):
                temp_value = self.plc_emulator.input_registers[i] / 100.0
                await node.write_value(temp_value)
            
            # Update pressure values
            for i, node in enumerate(self.nodes['pressures']):
                pressure_value = float(self.plc_emulator.input_registers[i + 10])
                await node.write_value(pressure_value)
            
            # Update flow values
            for i, node in enumerate(self.nodes['flows']):
                flow_value = self.plc_emulator.input_registers[i + 20] / 100.0
                await node.write_value(flow_value)
            
            # Update motor status
            for i, node in enumerate(self.nodes['motors']):
                await node.write_value(self.plc_emulator.coils[i])
            
            # Update discrete inputs
            for i, node in enumerate(self.nodes['discrete']):
                await node.write_value(self.plc_emulator.discrete_inputs[i])
            
            # Update setpoints
            for i, node in enumerate(self.nodes['setpoints']):
                setpoint_value = float(self.plc_emulator.holding_registers[i])
                await node.write_value(setpoint_value)
            
            # Update system status
            await self.nodes['status']['last_update'].write_value(datetime.now())
            
            # Simulate occasional communication errors
            comm_ok = random.random() > 0.01  # 1% chance of comm error
            await self.nodes['status']['comm_status'].write_value(comm_ok)
            
            if not comm_ok:
                current_errors = await self.nodes['status']['error_count'].read_value()
                await self.nodes['status']['error_count'].write_value(current_errors + 1)
                
        except Exception as e:
            logger.error(f"Error updating values: {e}")
    
    async def run(self):
        """Run the OPC UA server"""
        try:
            await self.init_server()
            
            async with self.server:
                logger.info("OPC UA Server started at opc.tcp://0.0.0.0:4840/freeopcua/server/")
                
                while True:
                    await self.update_values()
                    await asyncio.sleep(1)  # Update every second
                    
        except Exception as e:
            logger.error(f"Server error: {e}")
        finally:
            logger.info("OPC UA Server stopped")

if __name__ == "__main__":
    server = OPCUAServer()
    asyncio.run(server.run())