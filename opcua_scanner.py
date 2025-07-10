#!/usr/bin/env python3
"""
OPC UA Scanner/Client
Scans and monitors OPC UA servers
"""

import asyncio
import logging
import json
import time
from datetime import datetime
from asyncua import Client, ua
from asyncua.common.node import Node

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OPCUAScanner:
    def __init__(self, server_url="opc.tcp://localhost:4840/freeopcua/server/"):
        self.server_url = server_url
        self.client = None
        self.monitored_nodes = {}
        self.subscription = None
        
    async def connect(self):
        """Connect to OPC UA server"""
        try:
            self.client = Client(url=self.server_url)
            await self.client.connect()
            logger.info(f"Connected to OPC UA server: {self.server_url}")
            
            # Get server info
            server_info = await self.get_server_info()
            logger.info(f"Server info: {server_info}")
            
            return True
        except Exception as e:
            logger.error(f"Failed to connect to server: {e}")
            return False
    
    async def disconnect(self):
        """Disconnect from OPC UA server"""
        if self.client:
            try:
                await self.client.disconnect()
                logger.info("Disconnected from OPC UA server")
            except Exception as e:
                logger.error(f"Error disconnecting: {e}")
    
    async def get_server_info(self):
        """Get server information"""
        try:
            # Get server status
            server_status = await self.client.get_node("i=2259").read_value()  # Server_ServerStatus
            
            # Get server info
            info = {
                "server_state": str(server_status.State),
                "start_time": str(server_status.StartTime),
                "build_info": {
                    "product_name": str(server_status.BuildInfo.ProductName),
                    "product_uri": str(server_status.BuildInfo.ProductUri),
                    "manufacturer_name": str(server_status.BuildInfo.ManufacturerName),
                    "software_version": str(server_status.BuildInfo.SoftwareVersion),
                    "build_number": str(server_status.BuildInfo.BuildNumber),
                    "build_date": str(server_status.BuildInfo.BuildDate)
                }
            }
            return info
        except Exception as e:
            logger.error(f"Error getting server info: {e}")
            return {}
    
    async def browse_nodes(self, node=None, level=0):
        """Browse all nodes in the server"""
        if node is None:
            node = self.client.get_objects_node()
        
        nodes_info = []
        
        try:
            # Get node info
            node_info = {
                "node_id": str(node.nodeid),
                "browse_name": str(node.read_browse_name()),
                "display_name": str(node.read_display_name()),
                "node_class": str(node.read_node_class()),
                "level": level
            }
            
            # Try to read value if it's a variable
            try:
                if node.read_node_class() == ua.NodeClass.Variable:
                    value = await node.read_value()
                    data_type = await node.read_data_type_as_variant_type()
                    node_info["value"] = str(value)
                    node_info["data_type"] = str(data_type)
            except:
                pass
            
            nodes_info.append(node_info)
            
            # Browse children
            for child in await node.get_children():
                child_nodes = await self.browse_nodes(child, level + 1)
                nodes_info.extend(child_nodes)
                
        except Exception as e:
            logger.error(f"Error browsing node {node}: {e}")
        
        return nodes_info
    
    async def scan_all_nodes(self):
        """Scan all nodes and return structured data"""
        logger.info("Starting node scan...")
        all_nodes = await self.browse_nodes()
        
        # Organize nodes by type
        organized_nodes = {
            "folders": [],
            "variables": [],
            "objects": [],
            "methods": []
        }
        
        for node_info in all_nodes:
            node_class = node_info.get("node_class", "")
            if "Variable" in node_class:
                organized_nodes["variables"].append(node_info)
            elif "Object" in node_class:
                organized_nodes["objects"].append(node_info)
            elif "Method" in node_class:
                organized_nodes["methods"].append(node_info)
            else:
                organized_nodes["folders"].append(node_info)
        
        logger.info(f"Scan complete. Found {len(all_nodes)} nodes total")
        logger.info(f"Variables: {len(organized_nodes['variables'])}")
        logger.info(f"Objects: {len(organized_nodes['objects'])}")
        logger.info(f"Methods: {len(organized_nodes['methods'])}")
        
        return organized_nodes
    
    def print_scan_results(self, organized_nodes):
        """Print scan results in a readable format"""
        print("\n" + "="*80)
        print("OPC UA SERVER SCAN RESULTS")
        print("="*80)
        
        print(f"\nOBJECTS ({len(organized_nodes['objects'])}):")
        print("-" * 40)
        for obj in organized_nodes['objects']:
            indent = "  " * obj['level']
            print(f"{indent}{obj['display_name']} ({obj['node_id']})")
        
        print(f"\nVARIABLES ({len(organized_nodes['variables'])}):")
        print("-" * 40)
        for var in organized_nodes['variables']:
            indent = "  " * var['level']
            value = var.get('value', 'N/A')
            data_type = var.get('data_type', 'Unknown')
            print(f"{indent}{var['display_name']}: {value} [{data_type}]")
        
        print(f"\nMETHODS ({len(organized_nodes['methods'])}):")
        print("-" * 40)
        for method in organized_nodes['methods']:
            indent = "  " * method['level']
            print(f"{indent}{method['display_name']} ({method['node_id']})")
        
        print("\n" + "="*80)
    
    async def monitor_values(self, node_paths=None):
        """Monitor specific node values"""
        if not node_paths:
            # Default monitoring for PLC emulator
            node_paths = [
                "ns=2;s=PLC_System.Temperature_Sensors.Temperature_Sensor_00",
                "ns=2;s=PLC_System.Temperature_Sensors.Temperature_Sensor_01",
                "ns=2;s=PLC_System.Pressure_Sensors.Pressure_Sensor_00",
                "ns=2;s=PLC_System.Flow_Meters.Flow_Meter_00",
                "ns=2;s=PLC_System.Motor_Controls.Motor_00_Running",
                "ns=2;s=PLC_System.System_Status.PLC_Running",
                "ns=2;s=PLC_System.System_Status.Communication_OK",
                "ns=2;s=PLC_System.System_Status.Error_Count"
            ]
        
        logger.info("Starting value monitoring...")
        
        while True:
            try:
                print(f"\n{'='*60}")
                print(f"MONITORING UPDATE - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                print(f"{'='*60}")
                
                for node_path in node_paths:
                    try:
                        # Try to get node by browse path
                        node = self.client.get_node(node_path)
                        value = await node.read_value()
                        display_name = await node.read_display_name()
                        print(f"{display_name}: {value}")
                    except Exception as e:
                        print(f"Error reading {node_path}: {e}")
                
                await asyncio.sleep(2)  # Update every 2 seconds
                
            except KeyboardInterrupt:
                logger.info("Monitoring stopped by user")
                break
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(5)
    
    async def call_method(self, object_path, method_name, *args):
        """Call a method on the server"""
        try:
            obj_node = self.client.get_node(object_path)
            method_node = await obj_node.get_child(method_name)
            result = await obj_node.call_method(method_node, *args)
            logger.info(f"Method {method_name} called successfully: {result}")
            return result
        except Exception as e:
            logger.error(f"Error calling method {method_name}: {e}")
            return None

async def main():
    """Main scanner function"""
    scanner = OPCUAScanner("opc.tcp://opcua-server:4840/freeopcua/server/")
    
    # Try to connect
    if not await scanner.connect():
        logger.error("Failed to connect to server")
        return
    
    try:
        # Scan all nodes
        organized_nodes = await scanner.scan_all_nodes()
        scanner.print_scan_results(organized_nodes)
        
        # Save scan results to file
        with open('/app/scan_results.json', 'w') as f:
            json.dump(organized_nodes, f, indent=2)
        logger.info("Scan results saved to scan_results.json")
        
        # Test method call
        print("\nTesting method call...")
        result = await scanner.call_method("2:PLC_System", "2:RestartPLC", True)
        print(f"Method call result: {result}")
        
        # Start monitoring
        print("\nStarting continuous monitoring (Ctrl+C to stop)...")
        await scanner.monitor_values()
        
    except KeyboardInterrupt:
        logger.info("Scanner stopped by user")
    except Exception as e:
        logger.error(f"Scanner error: {e}")
    finally:
        await scanner.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
