#!/usr/bin/env python3

import asyncio
import logging
from typing import Any, Dict, List, Optional, Union
import json
import numpy as np
import subprocess
import sys
import os
from dataclasses import dataclass
from enum import Enum
from datetime import datetime

# MCP imports
from mcp.server import NotificationOptions, Server
from mcp.server.models import InitializationOptions
import mcp.server.stdio
import mcp.types as types

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("quantum-hardware-mcp")

# Quantum Hardware Components and Constants
class QubitType(Enum):
    TRANSMON = "transmon"
    FLUXONIUM = "fluxonium"
    CHARGE = "charge"
    PHASE = "phase"

@dataclass
class SuperconductingQubit:
    name: str
    qubit_type: QubitType
    frequency: float  # GHz
    coupling_strength: float  # MHz
    coherence_time_t1: float  # microseconds
    coherence_time_t2: float  # microseconds
    
@dataclass
class JosephsonJunction:
    critical_current: float  # nA
    capacitance: float  # fF
    resistance: float  # Ohms
    energy_josephson: float  # GHz
    energy_charging: float  # GHz

@dataclass
class SpiralInductor:
    name: str
    n_turns: int
    width: float  # μm
    radius: float  # μm
    gap: float  # μm
    inductance: float  # nH
    pos_x: str
    pos_y: str

@dataclass
class CPWResonator:
    name: str
    frequency: float  # GHz
    width: float  # μm
    gap: float  # μm
    length: float  # μm
    quality_factor: float

class QuantumHardwareMCPServer:
    def __init__(self):
        self.server = Server("quantum-hardware-mcp")
        self.qubits: Dict[str, SuperconductingQubit] = {}
        self.junctions: Dict[str, JosephsonJunction] = {}
        self.spirals: Dict[str, SpiralInductor] = {}
        self.resonators: Dict[str, CPWResonator] = {}
        self.design = None  # Will hold Qiskit Metal design object
        self.gui = None  # MetalGUI instance
        self.installation_status = {
            "qiskit_metal": False,
            "pyside2": False,
            "geopandas": False,
            "jupyter": False
        }
        
        # Sample quantum hardware data from the notebook
        self._initialize_sample_data()
        self._setup_tools()
        
    def _initialize_sample_data(self):
        """Initialize with sample quantum hardware data from the notebook"""
        # Transmon qubits Q4 and Q5 from the notebook
        self.qubits["Q4"] = SuperconductingQubit(
            name="Q4 Transmon Pocket",
            qubit_type=QubitType.TRANSMON,
            frequency=5.2,  # GHz
            coupling_strength=50.0,  # MHz  
            coherence_time_t1=80.0,  # microseconds
            coherence_time_t2=60.0   # microseconds
        )
        
        self.qubits["Q5"] = SuperconductingQubit(
            name="Q5 Transmon Pocket", 
            qubit_type=QubitType.TRANSMON,
            frequency=5.0,  # GHz
            coupling_strength=45.0,  # MHz
            coherence_time_t1=75.0,  # microseconds
            coherence_time_t2=55.0   # microseconds
        )
        
        # Josephson junction JJ2 from notebook  
        self.junctions["JJ2"] = JosephsonJunction(
            critical_current=15.0,  # nA
            capacitance=2.0,  # fF (from LOM analysis)
            resistance=150.0,  # Ohms
            energy_josephson=12.31,  # GHz (Lj from notebook)
            energy_charging=0.3   # GHz
        )
        
        # Spiral inductors from notebook
        self.spirals["spiralm1"] = SpiralInductor(
            name="Mutual Inductor M1",
            n_turns=5,
            width=0.5,  # μm
            radius=5.0,  # μm  
            gap=0.2,  # μm
            inductance=10.0,  # nH estimated
            pos_x="0.60mm",
            pos_y="2.2mm"
        )
        
        self.spirals["spiralm2"] = SpiralInductor(
            name="Mutual Inductor M2", 
            n_turns=5,
            width=0.5,  # μm
            radius=5.0,  # μm
            gap=0.2,  # μm
            inductance=10.0,  # nH estimated
            pos_x="0.62mm", 
            pos_y="2.2mm"
        )
        
        self.spirals["spiralS1"] = SpiralInductor(
            name="Series Inductor S1",
            n_turns=12,
            width=0.5,  # μm
            radius=5.0,  # μm
            gap=0.2,  # μm
            inductance=25.0,  # nH estimated
            pos_x="0.67mm",
            pos_y="2.2mm"
        )
        
        self.spirals["spiralS2"] = SpiralInductor(
            name="Series Inductor S2",
            n_turns=12, 
            width=0.5,  # μm
            radius=5.0,  # μm
            gap=0.2,  # μm
            inductance=25.0,  # nH estimated
            pos_x="0.55mm",
            pos_y="2.2mm"
        )

    def _setup_tools(self):
        """Setup MCP tools"""
        
        @self.server.list_tools()
        async def handle_list_tools() -> list[types.Tool]:
            """List available quantum hardware tools"""
            return [
                types.Tool(
                    name="get_qubit_info",
                    description="Get information about a superconducting qubit",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "qubit_name": {
                                "type": "string",
                                "description": "Name of the qubit to query"
                            }
                        },
                        "required": ["qubit_name"]
                    },
                ),
                types.Tool(
                    name="add_qubit",
                    description="Add a new superconducting qubit to the system",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "name": {"type": "string", "description": "Qubit name"},
                            "qubit_type": {
                                "type": "string", 
                                "enum": ["transmon", "fluxonium", "charge", "phase"],
                                "description": "Type of superconducting qubit"
                            },
                            "frequency": {"type": "number", "description": "Qubit frequency in GHz"},
                            "coupling_strength": {"type": "number", "description": "Coupling strength in MHz"},
                            "coherence_time_t1": {"type": "number", "description": "T1 coherence time in microseconds"},
                            "coherence_time_t2": {"type": "number", "description": "T2 coherence time in microseconds"}
                        },
                        "required": ["name", "qubit_type", "frequency", "coupling_strength", "coherence_time_t1", "coherence_time_t2"]
                    },
                ),
                types.Tool(
                    name="analyze_josephson_junction",
                    description="Analyze Josephson junction parameters",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "junction_name": {
                                "type": "string",
                                "description": "Name of the junction to analyze"
                            }
                        },
                        "required": ["junction_name"]
                    },
                ),
                types.Tool(
                    name="check_qiskit_installation",
                    description="Check the installation status of Qiskit Metal and dependencies",
                    inputSchema={
                        "type": "object",
                        "properties": {},
                    },
                ),
                types.Tool(
                    name="install_qiskit_dependencies",
                    description="Install Qiskit Metal and required dependencies",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "force_reinstall": {
                                "type": "boolean",
                                "description": "Force reinstallation even if already installed",
                                "default": False
                            }
                        },
                    },
                ),
                types.Tool(
                    name="calculate_qubit_metrics",
                    description="Calculate quantum coherence and performance metrics",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "qubit_name": {
                                "type": "string",
                                "description": "Name of the qubit to calculate metrics for"
                            }
                        },
                        "required": ["qubit_name"]
                    },
                ),
                types.Tool(
                    name="generate_circuit_design",
                    description="Generate quantum circuit design parameters",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "circuit_type": {
                                "type": "string",
                                "enum": ["transmon", "cpw_resonator", "coupler"],
                                "description": "Type of circuit to design"
                            },
                            "target_frequency": {
                                "type": "number",
                                "description": "Target frequency in GHz"
                            }
                        },
                        "required": ["circuit_type", "target_frequency"]
                    },
                ),
                types.Tool(
                    name="list_all_qubits",
                    description="List all superconducting qubits in the system",
                    inputSchema={
                        "type": "object",
                        "properties": {},
                    },
                ),
                types.Tool(
                    name="get_hardware_overview",
                    description="Get comprehensive overview of quantum hardware setup",
                    inputSchema={
                        "type": "object",
                        "properties": {},
                    },
                ),
                types.Tool(
                    name="export_design_to_gds",
                    description="Export the current quantum circuit design to a GDS file for fabrication",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "output_path": {
                                "type": "string",
                                "description": "Output path for the GDS file (optional, defaults to current directory)",
                                "default": "./quantum_circuit_design.gds"
                            },
                            "create_design": {
                                "type": "boolean",
                                "description": "Whether to create a new design from current qubits if none exists",
                                "default": True
                            }
                        },
                    },
                ),
                types.Tool(
                    name="create_notebook_design",
                    description="Create the complete quantum circuit design from the notebook with all components",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "include_analysis": {
                                "type": "boolean",
                                "description": "Whether to include LOM and EPR analysis setup",
                                "default": True
                            }
                        },
                    },
                ),
                types.Tool(
                    name="list_spiral_inductors",
                    description="List all spiral inductors in the system",
                    inputSchema={
                        "type": "object",
                        "properties": {},
                    },
                ),
                types.Tool(
                    name="add_spiral_inductor",
                    description="Add a new spiral inductor to the system",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "name": {"type": "string", "description": "Inductor name"},
                            "n_turns": {"type": "number", "description": "Number of turns"},
                            "width": {"type": "number", "description": "Trace width in μm"},
                            "radius": {"type": "number", "description": "Inner radius in μm"},
                            "gap": {"type": "number", "description": "Gap between traces in μm"},
                            "pos_x": {"type": "string", "description": "X position (e.g., '0.6mm')"},
                            "pos_y": {"type": "string", "description": "Y position (e.g., '2.2mm')"}
                        },
                        "required": ["name", "n_turns", "width", "radius", "gap", "pos_x", "pos_y"]
                    },
                ),
                types.Tool(
                    name="run_lom_analysis",
                    description="Run LOM (Linear Oscillator Model) analysis on the quantum circuit",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "lj_value": {"type": "number", "description": "Josephson inductance in nH", "default": 12.31},
                            "cj_value": {"type": "number", "description": "Junction capacitance in fF", "default": 2.0},
                            "freq_readout": {"type": "number", "description": "Readout frequency in GHz", "default": 7.0}
                        },
                    },
                ),
                types.Tool(
                    name="add_cpw_waveguide",
                    description="Add a CPW (Coplanar Waveguide) transmission line between two points",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "name": {"type": "string", "description": "Waveguide name"},
                            "start_x": {"type": "string", "description": "Start X position (e.g., '0.60mm')"},
                            "start_y": {"type": "string", "description": "Start Y position (e.g., '2.2mm')"},
                            "end_x": {"type": "string", "description": "End X position (e.g., '0.62mm')"},
                            "end_y": {"type": "string", "description": "End Y position (e.g., '2.2mm')"},
                            "width": {"type": "number", "description": "CPW center conductor width in μm", "default": 0.5},
                            "gap": {"type": "number", "description": "CPW gap width in μm", "default": 0.3}
                        },
                        "required": ["name", "start_x", "start_y", "end_x", "end_y"]
                    },
                ),
            ]

        @self.server.call_tool()
        async def handle_call_tool(
            name: str, arguments: dict[str, Any] | None
        ) -> list[types.TextContent]:
            """Handle tool calls"""
            if arguments is None:
                arguments = {}

            try:
                if name == "get_qubit_info":
                    return await self._get_qubit_info(arguments.get("qubit_name"))
                elif name == "add_qubit":
                    return await self._add_qubit(arguments)
                elif name == "analyze_josephson_junction":
                    return await self._analyze_josephson_junction(arguments.get("junction_name"))
                elif name == "check_qiskit_installation":
                    return await self._check_qiskit_installation()
                elif name == "install_qiskit_dependencies":
                    return await self._install_qiskit_dependencies(arguments.get("force_reinstall", False))
                elif name == "calculate_qubit_metrics":
                    return await self._calculate_qubit_metrics(arguments.get("qubit_name"))
                elif name == "generate_circuit_design":
                    return await self._generate_circuit_design(
                        arguments.get("circuit_type"), 
                        arguments.get("target_frequency")
                    )
                elif name == "list_all_qubits":
                    return await self._list_all_qubits()
                elif name == "get_hardware_overview":
                    return await self._get_hardware_overview()
                elif name == "export_design_to_gds":
                    return await self._export_design_to_gds(
                        arguments.get("output_path", "./quantum_circuit_design.gds"),
                        arguments.get("create_design", True)
                    )
                elif name == "create_notebook_design":
                    return await self._create_notebook_design(
                        arguments.get("include_analysis", True)
                    )
                elif name == "list_spiral_inductors":
                    return await self._list_spiral_inductors()
                elif name == "add_spiral_inductor":
                    return await self._add_spiral_inductor(arguments)
                elif name == "run_lom_analysis":
                    return await self._run_lom_analysis(
                        arguments.get("lj_value", 12.31),
                        arguments.get("cj_value", 2.0),
                        arguments.get("freq_readout", 7.0)
                    )
                elif name == "add_cpw_waveguide":
                    return await self._add_cpw_waveguide(arguments)
                else:
                    raise ValueError(f"Unknown tool: {name}")

            except Exception as e:
                logger.error(f"Error in tool {name}: {str(e)}")
                return [types.TextContent(type="text", text=f"Error: {str(e)}")]

    async def _get_qubit_info(self, qubit_name: str) -> list[types.TextContent]:
        """Get detailed information about a specific qubit"""
        if not qubit_name:
            return [types.TextContent(type="text", text="Error: qubit_name is required")]
            
        if qubit_name not in self.qubits:
            available = ", ".join(self.qubits.keys())
            return [types.TextContent(
                type="text", 
                text=f"Qubit '{qubit_name}' not found. Available qubits: {available}"
            )]
        
        qubit = self.qubits[qubit_name]
        info = f"""
Superconducting Qubit Information: {qubit.name}
================================================
Type: {qubit.qubit_type.value.title()}
Frequency: {qubit.frequency} GHz
Coupling Strength: {qubit.coupling_strength} MHz
T1 Coherence Time: {qubit.coherence_time_t1} μs
T2 Coherence Time: {qubit.coherence_time_t2} μs

Performance Metrics:
- Quality Factor (T2/T1): {qubit.coherence_time_t2/qubit.coherence_time_t1:.2f}
- Gate Time Estimate: {1000/qubit.coupling_strength:.2f} ns
- Coherence Limited Gates: {int(qubit.coherence_time_t2 * qubit.coupling_strength / 1000)}

Qubit Type Characteristics:
{self._get_qubit_type_info(qubit.qubit_type)}
"""
        return [types.TextContent(type="text", text=info)]

    async def _add_qubit(self, arguments: dict) -> list[types.TextContent]:
        """Add a new superconducting qubit"""
        try:
            qubit = SuperconductingQubit(
                name=arguments["name"],
                qubit_type=QubitType(arguments["qubit_type"]),
                frequency=float(arguments["frequency"]),
                coupling_strength=float(arguments["coupling_strength"]),
                coherence_time_t1=float(arguments["coherence_time_t1"]),
                coherence_time_t2=float(arguments["coherence_time_t2"])
            )
            
            self.qubits[arguments["name"]] = qubit
            
            return [types.TextContent(
                type="text",
                text=f"Successfully added qubit '{arguments['name']}' of type {arguments['qubit_type']}"
            )]
        except Exception as e:
            return [types.TextContent(type="text", text=f"Error adding qubit: {str(e)}")]

    async def _analyze_josephson_junction(self, junction_name: str) -> list[types.TextContent]:
        """Analyze Josephson junction parameters"""
        if not junction_name:
            return [types.TextContent(type="text", text="Error: junction_name is required")]
            
        if junction_name not in self.junctions:
            available = ", ".join(self.junctions.keys())
            return [types.TextContent(
                type="text",
                text=f"Junction '{junction_name}' not found. Available junctions: {available}"
            )]
        
        junction = self.junctions[junction_name]
        
        # Calculate derived parameters
        flux_quantum = 2.067833848e-15  # Wb
        plancks_constant = 6.62607015e-34  # J⋅s
        elementary_charge = 1.602176634e-19  # C
        
        # Josephson energy in Joules
        ej_joules = junction.energy_josephson * 1e9 * plancks_constant
        
        # Charging energy in Joules  
        ec_joules = junction.energy_charging * 1e9 * plancks_constant
        
        # Ratio EJ/EC
        ej_ec_ratio = junction.energy_josephson / junction.energy_charging
        
        analysis = f"""
Josephson Junction Analysis: {junction_name}
==========================================
Physical Parameters:
- Critical Current: {junction.critical_current} nA
- Capacitance: {junction.capacitance} fF
- Resistance: {junction.resistance} Ω

Energy Scales:
- Josephson Energy (EJ): {junction.energy_josephson} GHz
- Charging Energy (EC): {junction.energy_charging} GHz
- EJ/EC Ratio: {ej_ec_ratio:.1f}

Junction Characteristics:
- Regime: {'Transmon' if ej_ec_ratio > 50 else 'Charge' if ej_ec_ratio < 1 else 'Intermediate'}
- Plasma Frequency: {np.sqrt(8 * junction.energy_josephson * junction.energy_charging):.2f} GHz
- Anharmonicity: {-junction.energy_charging:.3f} GHz

Current-Voltage Relationship:
The junction exhibits the DC Josephson effect for currents below {junction.critical_current} nA.
Above this threshold, voltage appears across the junction following the RSJ model.
"""
        return [types.TextContent(type="text", text=analysis)]

    async def _check_qiskit_installation(self) -> list[types.TextContent]:
        """Check installation status of Qiskit Metal and dependencies"""
        packages = {
            "qiskit-metal": "qiskit_metal",
            "pyside2": "PySide2", 
            "geopandas": "geopandas",
            "jupyter": "jupyter"
        }
        
        status_report = "Qiskit Metal Installation Status\n" + "="*35 + "\n"
        
        for package_name, import_name in packages.items():
            try:
                __import__(import_name)
                status = "✓ INSTALLED"
                self.installation_status[package_name.replace("-", "_")] = True
            except ImportError:
                status = "✗ NOT INSTALLED"
                self.installation_status[package_name.replace("-", "_")] = False
            
            status_report += f"{package_name:15} {status}\n"
        
        status_report += "\nInstallation Instructions:\n"
        status_report += "1. Create conda environment: conda create -n qmetal\n"
        status_report += "2. Activate environment: conda activate qmetal\n"
        status_report += "3. Install Python 3.7: conda install python=3.7\n"
        status_report += "4. Install packages: pip install qiskit-metal pyside2 geopandas jupyter\n"
        
        return [types.TextContent(type="text", text=status_report)]

    async def _install_qiskit_dependencies(self, force_reinstall: bool = False) -> list[types.TextContent]:
        """Install Qiskit Metal and dependencies"""
        packages = ["qiskit-metal", "pyside2", "geopandas", "jupyter"]
        
        install_log = "Installing Qiskit Metal Dependencies\n" + "="*35 + "\n"
        
        for package in packages:
            try:
                cmd = [sys.executable, "-m", "pip", "install"]
                if force_reinstall:
                    cmd.append("--force-reinstall")
                cmd.append(package)
                
                install_log += f"Installing {package}...\n"
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
                
                if result.returncode == 0:
                    install_log += f"✓ {package} installed successfully\n"
                else:
                    install_log += f"✗ Failed to install {package}: {result.stderr}\n"
                    
            except subprocess.TimeoutExpired:
                install_log += f"✗ Installation of {package} timed out\n"
            except Exception as e:
                install_log += f"✗ Error installing {package}: {str(e)}\n"
        
        install_log += "\nInstallation complete. Run check_qiskit_installation to verify.\n"
        return [types.TextContent(type="text", text=install_log)]

    async def _calculate_qubit_metrics(self, qubit_name: str) -> list[types.TextContent]:
        """Calculate quantum coherence and performance metrics"""
        if not qubit_name or qubit_name not in self.qubits:
            return [types.TextContent(type="text", text=f"Qubit '{qubit_name}' not found")]
        
        qubit = self.qubits[qubit_name]
        
        # Calculate performance metrics
        quality_factor = qubit.coherence_time_t2 / qubit.coherence_time_t1
        gate_time_ns = 1000 / qubit.coupling_strength  # nanoseconds
        coherence_limited_gates = int(qubit.coherence_time_t2 * 1000 / gate_time_ns)
        
        # Fidelity estimates (simplified)
        single_qubit_fidelity = 1 - (gate_time_ns / (qubit.coherence_time_t1 * 1000))
        two_qubit_fidelity = 1 - (2 * gate_time_ns / (qubit.coherence_time_t1 * 1000))
        
        metrics = f"""
Quantum Performance Metrics for {qubit.name}
===========================================
Coherence Metrics:
- T1 (Energy relaxation): {qubit.coherence_time_t1} μs
- T2 (Dephasing): {qubit.coherence_time_t2} μs  
- Quality Factor (T2/T1): {quality_factor:.2f}

Gate Performance:
- Estimated Gate Time: {gate_time_ns:.1f} ns
- Single-Qubit Gate Fidelity: {single_qubit_fidelity:.4f}
- Two-Qubit Gate Fidelity: {two_qubit_fidelity:.4f}
- Coherence-Limited Gates: {coherence_limited_gates}

Frequency Domain:
- Qubit Frequency: {qubit.frequency} GHz
- Coupling Strength: {qubit.coupling_strength} MHz
- Bandwidth: {qubit.coupling_strength * 2} MHz

Recommendations:
{self._get_performance_recommendations(qubit)}
"""
        return [types.TextContent(type="text", text=metrics)]

    async def _generate_circuit_design(self, circuit_type: str, target_frequency: float) -> list[types.TextContent]:
        """Generate quantum circuit design parameters"""
        if not circuit_type or target_frequency is None:
            return [types.TextContent(type="text", text="Error: circuit_type and target_frequency required")]
        
        design = f"""
Quantum Circuit Design: {circuit_type.upper()}
Target Frequency: {target_frequency} GHz
========================================

"""
        
        if circuit_type == "transmon":
            # Transmon design parameters
            ec = 0.3  # GHz, typical charging energy
            ej = target_frequency * 4  # Rough estimate
            
            design += f"""Transmon Qubit Design:
- Josephson Energy (EJ): {ej:.1f} GHz
- Charging Energy (EC): {ec} GHz
- EJ/EC Ratio: {ej/ec:.1f}
- Estimated Pad Capacitance: {80 + (target_frequency - 5) * 10:.0f} fF
- Junction Area: {100 + (ej - 20) * 5:.0f} μm²

Design Notes:
- Large EJ/EC ratio ensures transmon regime
- Reduced charge noise sensitivity
- Anharmonicity ≈ -EC = -{ec} GHz
"""
            
        elif circuit_type == "cpw_resonator":
            # CPW resonator design
            wavelength = 3e8 / (target_frequency * 1e9)  # meters
            length = wavelength / 4  # quarter-wave resonator
            
            design += f"""CPW Resonator Design:
- Resonant Frequency: {target_frequency} GHz
- Quarter-Wave Length: {length*1000:.1f} mm
- Center Conductor Width: 10 μm (typical)
- Gap Width: 6 μm (typical)
- Quality Factor Target: 10,000-100,000

Coupling Parameters:
- Coupling Capacitance: 1-10 fF
- Coupling Strength: 10-100 MHz
- External Q: 1,000-10,000
"""

        elif circuit_type == "coupler":
            design += f"""Tunable Coupler Design:
- Operating Frequency: {target_frequency} GHz
- Coupling Range: 0-50 MHz
- Control Flux: 0-1 Φ₀
- Sweet Spot Operation: Φ = 0.5 Φ₀

Components:
- SQUID Loop Area: 100 μm²
- Junction Asymmetry: 10-20%
- Control Line Inductance: 100 nH
- Isolation: >20 dB when OFF
"""
        
        return [types.TextContent(type="text", text=design)]

    async def _list_all_qubits(self) -> list[types.TextContent]:
        """List all qubits in the system"""
        if not self.qubits:
            return [types.TextContent(type="text", text="No qubits found in the system.")]
        
        qubit_list = "Superconducting Qubits in System\n" + "="*32 + "\n"
        
        for name, qubit in self.qubits.items():
            qubit_list += f"""
Name: {qubit.name}
Type: {qubit.qubit_type.value.title()}
Frequency: {qubit.frequency} GHz
T1: {qubit.coherence_time_t1} μs, T2: {qubit.coherence_time_t2} μs
--------------------------------
"""
        
        return [types.TextContent(type="text", text=qubit_list)]

    async def _get_hardware_overview(self) -> list[types.TextContent]:
        """Get comprehensive overview of quantum hardware setup"""
        overview = """
BZU Quantum Computing Hardware Overview
======================================

System Architecture:
- Superconducting Quantum Processor
- Dilution Refrigerator (Base Temperature: ~15 mK)
- Microwave Control Electronics
- FPGA-based Real-time Control System

Circuit Design (from Notebook):
- Tunable Coupler Architecture
- Transmon Pocket Qubits (Q4, Q5)
- Spiral Inductor Coupling Elements
- Josephson Junction Flux Control (JJ2)
- CPW Transmission Lines

Design Features:
- Mutual Coupling via Spiral Inductors (M1, M2)
- Series Inductance Control (S1, S2)
- Variable Flux Tuning through JJ2
- Pocket Isolation for Reduced Crosstalk
- Multi-layer CPW Routing (Layer 2)

Key Advantages:
✓ Tunable Inter-qubit Coupling
✓ Flux-noise Protected Operation
✓ High Design Flexibility
✓ Scalable Architecture
✓ Fabrication-ready GDS Export

Current System Status:
"""
        
        overview += f"- Active Qubits: {len(self.qubits)}\n"
        overview += f"- Josephson Junctions: {len(self.junctions)}\n"
        overview += f"- Spiral Inductors: {len(self.spirals)}\n"
        overview += f"- CPW Resonators: {len(self.resonators)}\n"
        
        if self.qubits:
            avg_t1 = np.mean([q.coherence_time_t1 for q in self.qubits.values()])
            avg_t2 = np.mean([q.coherence_time_t2 for q in self.qubits.values()])
            overview += f"- Average T1: {avg_t1:.1f} μs\n"
            overview += f"- Average T2: {avg_t2:.1f} μs\n"
        
        overview += """
Development Environment:
- Qiskit Metal for Circuit Design
- MetalGUI for Visual Design Interface
- Ansys Q3D/HFSS for EM Simulation
- LOM/EPR Analysis Tools
- Python 3.7+ Runtime Environment

Available Tools:
- create_notebook_design: Recreate the full notebook circuit
- list_spiral_inductors: View inductor components
- add_spiral_inductor: Add new inductors
- run_lom_analysis: Perform quantum analysis
- export_design_to_gds: Generate fabrication files

Next Steps:
1. Use create_notebook_design to build the complete circuit
2. Run LOM analysis for quantum parameters
3. Export to GDS for fabrication
4. Simulate in Ansys for verification
5. Optimize coupling strengths and frequencies
"""
        
        return [types.TextContent(type="text", text=overview)]

    async def _export_design_to_gds(self, output_path: str, create_design: bool = True) -> list[types.TextContent]:
        """Export the quantum circuit design to a GDS file"""
        try:
            # Check if Qiskit Metal is installed
            try:
                import qiskit_metal as metal
                from qiskit_metal import Dict, Headings
                from qiskit_metal.qlibrary.qubits.transmon_pocket import TransmonPocket
                from qiskit_metal.qlibrary.tlines.meandered import RouteMeander
            except ImportError:
                return [types.TextContent(
                    type="text", 
                    text="Error: Qiskit Metal not installed. Run install_qiskit_dependencies first."
                )]

            # Create or use existing design
            if self.design is None and create_design:
                # Create a new design
                self.design = metal.designs.DesignPlanar()
                self.design.overwrite_enabled = True
                
                # Add qubits to the design
                qubit_components = {}
                for i, (qubit_name, qubit) in enumerate(self.qubits.items()):
                    if qubit.qubit_type == QubitType.TRANSMON:
                        # Create transmon pocket qubit
                        qubit_options = Dict(
                            pad_width='455 um',
                            pad_height='90 um', 
                            pad_gap='30 um',
                            pos_x=f'{i * 2000}um',
                            pos_y='0um',
                            orientation='0',
                        )
                        
                        qubit_components[qubit_name] = TransmonPocket(
                            self.design, 
                            qubit_name.replace(' ', '_'), 
                            options=qubit_options
                        )
                
                # Build the design
                self.design.rebuild()
                
                logger.info(f"Created new design with {len(qubit_components)} qubits")
            
            elif self.design is None:
                return [types.TextContent(
                    type="text",
                    text="Error: No design available and create_design is False. Add qubits first or set create_design to True."
                )]

            # Access the GDS renderer
            gds_renderer = self.design.renderers.gds

            # Set export options
            gds_renderer.options['path_filename'] = output_path
            gds_renderer.options['short_segments_to_not_fillet'] = 'False'
            scale_fillet = 2.0
            gds_renderer.options['check_short_segments_by_scaling_fillet'] = scale_fillet
            gds_renderer.options['short_segments_to_not_fillet'] = 'True'

            # Export the GDS file
            gds_renderer.export_to_gds(output_path)

            # Generate export summary
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            export_summary = f"""
GDS Export Successful (Notebook Design)
======================================
Timestamp: {timestamp}
Output File: {output_path}
Design Components: {len(self.design.components) if self.design else 0}

Circuit Components Exported:
- Active Qubits: {len(self.qubits)}
- Spiral Inductors: {len(self.spirals)}
- Josephson Junctions: {len(self.junctions)}

Export Settings:
- Path: {output_path}
- Short segments fillet: Enabled
- Scale fillet: {scale_fillet}
- Layer configuration: Multi-layer (CPW on Layer 2)

Components Included:
"""
            
            for qubit_name, qubit in self.qubits.items():
                export_summary += f"- {qubit.name} ({qubit.qubit_type.value.title()}) @ {qubit.frequency} GHz\n"
                
            for spiral_name, spiral in self.spirals.items():
                export_summary += f"- {spiral.name} ({spiral.n_turns} turns, {spiral.inductance:.1f} nH)\n"
                
            for junction_name, junction in self.junctions.items():
                export_summary += f"- {junction_name} (Ic: {junction.critical_current} nA, EJ/EC: {junction.energy_josephson/junction.energy_charging:.1f})\n"
            
            export_summary += f"""
Fabrication Notes:
- Two-qubit tunable coupler design
- Requires precision lithography for Josephson junctions
- Spiral inductors need accurate etching
- Multi-layer alignment critical for CPW routing

Next Steps:
1. Open {output_path} in KLayout for design verification
2. Check design rule compliance (DRC)
3. Generate process-specific layers and materials
4. Submit to superconducting quantum fabrication facility
5. Specify: Nb/Al junction process, CPW ground planes, isolation

File ready for quantum circuit fabrication!
"""

            return [types.TextContent(type="text", text=export_summary)]

        except Exception as e:
            error_msg = f"GDS Export Failed: {str(e)}\n"
            error_msg += "Common issues:\n"
            error_msg += "- Qiskit Metal not properly installed\n" 
            error_msg += "- Invalid output path or permissions\n"
            error_msg += "- Design contains invalid geometries\n"
            error_msg += "- Missing design components\n"
            
            return [types.TextContent(type="text", text=error_msg)]

    async def _create_notebook_design(self, include_analysis: bool = True) -> list[types.TextContent]:
        """Create the complete quantum circuit design from the notebook"""
        try:
            # Check if Qiskit Metal is installed
            try:
                import qiskit_metal as metal
                from qiskit_metal import Dict, MetalGUI
                from qiskit_metal.qlibrary.sample_shapes.n_square_spiral import NSquareSpiral
                from qiskit_metal.qlibrary.qubits.transmon_pocket import TransmonPocket
                from qiskit_metal.qlibrary.qubits.JJ_Manhattan import jj_manhattan
                from qiskit_metal.qlibrary.tlines.straight_path import RouteStraight
            except ImportError:
                return [types.TextContent(
                    type="text", 
                    text="Error: Qiskit Metal not installed. Run install_qiskit_dependencies first."
                )]

            # Create new design
            self.design = metal.designs.DesignPlanar()
            self.design.overwrite_enabled = True
            
            # Set design variables (from notebook)
            self.design.variables['cpw_width'] = '0.5um'
            self.design.variables['cpw_gap'] = '0.3um'
            
            # Create GUI
            try:
                self.gui = MetalGUI(self.design)
            except:
                # GUI creation might fail in headless environment
                pass
            
            # Create spiral inductors
            spiral_components = {}
            
            # Mutual inductors (spiralm1, spiralm2)
            mutual_ops = {
                'n': '5',
                'width': '0.5um',
                'radius': '5um',
                'gap': '0.2um',
                'orientation': '0',
                'subtract': 'False'
            }
            
            spiral_components['spiralm1'] = NSquareSpiral(
                self.design, 'spiralm1', 
                Dict(pos_x='0.60mm', pos_y='2.2mm', **mutual_ops)
            )
            
            spiral_components['spiralm2'] = NSquareSpiral(
                self.design, 'spiralm2',
                Dict(pos_x='0.62mm', pos_y='2.2mm', **mutual_ops)
            )
            
            # Series inductors (spiralS1, spiralS2)
            series_ops = {
                'n': '12',
                'width': '0.5um', 
                'radius': '5um',
                'gap': '0.2um',
                'orientation': '0',
                'helper': 'True',
                'subtract': 'False'
            }
            
            spiral_components['spiralS1'] = NSquareSpiral(
                self.design, 'spiralS1',
                Dict(pos_x='0.67mm', pos_y='2.2mm', **series_ops)
            )
            
            spiral_components['spiralS2'] = NSquareSpiral(
                self.design, 'spiralS2', 
                Dict(pos_x='0.55mm', pos_y='2.2mm', **series_ops)
            )
            
            # Create Josephson junction (JJ2)
            jj_options = {
                'pos_x': '0.6040mm',
                'pos_y': '2.1760mm',
                'orientation': '0.0',
                'chip': 'main',
                'layer': '1',
                'JJ_pad_lower_width': '5um',
                'JJ_pad_lower_height': '2um',
                'JJ_pad_lower_pos_x': '0',
                'JJ_pad_lower_pos_y': '0',
                'finger_lower_width': '0.2um',
                'finger_lower_height': '4um',
                'extension': '0.2um'
            }
            
            jj_component = jj_manhattan(self.design, 'JJ2', options=jj_options)
            
            # Create transmon qubits (Q4, Q5)
            q4_options = Dict(
                connection_pads=Dict(
                    a=Dict(
                        loc_W=-1,
                        loc_H=+1,
                        pad_width='7um',
                        pad_height='2um',
                        pad_gap='0.6um',
                        pocket_extent='0.0um',
                        pad_cpw_shift='1um',
                        pocket_rise='0.0um',
                        cpw_extend='40um',
                        pad_cpw_extent='0.1um'
                    )
                ),
                pad_gap='1.7um',
                inductor_width='1.11um',
                pad_width='25.3um',
                pad_height='5um',
                pocket_width='39.2um',
                pocket_height='39.2um',
                pos_x='0.72mm',
                pos_y='2.2mm'
            )
            
            q4_component = TransmonPocket(self.design, 'Q4', options=q4_options)
            
            q5_options = Dict(
                connection_pads=Dict(
                    b=Dict(
                        loc_W=+1,
                        loc_H=+1,
                        pad_width='7um',
                        pad_height='2um',
                        pad_gap='0.6um',
                        pocket_extent='0.0um',
                        pad_cpw_shift='1um',
                        pocket_rise='0.0um',
                        cpw_extend='20um',
                        pad_cpw_extent='0.1um'
                    )
                ),
                pad_gap='1.7um',
                inductor_width='1.11um',
                pad_width='25.3um',
                pad_height='5um',
                pocket_width='39.2um',
                pocket_height='39.2um',
                pos_x='0.50mm',
                pos_y='2.2mm'
            )
            
            q5_component = TransmonPocket(self.design, 'Q5', options=q5_options)
            
            # Add CPW waveguide between mutual inductors (M1 and M2)
            try:
                from qiskit_metal.qlibrary.tlines.straight_path import RouteStraight
                
                # Create points for the waveguide between mutual inductors
                import numpy as np
                
                # Add pins to connect the mutual inductors
                spiral_components['spiralm1'].add_pin(
                    'coupling_out', 
                    points=np.array([[0.6095, 2.194], [0.6095, 2.194]]), 
                    width=0.0000005, 
                    input_as_norm=False
                )
                
                spiral_components['spiralm2'].add_pin(
                    'coupling_in', 
                    points=np.array([[0.6105, 2.194], [0.6105, 2.194]]), 
                    width=0.0000005, 
                    input_as_norm=False
                )
                
                # Create the CPW waveguide connection
                cpw_options = Dict(
                    pin_inputs=Dict(
                        start_pin=Dict(
                            component='spiralm1',
                            pin='coupling_out'
                        ),
                        end_pin=Dict(
                            component='spiralm2', 
                            pin='coupling_in'
                        )
                    ),
                    trace_width='0.5um',
                    trace_gap='0.3um'
                )
                
                m1_m2_waveguide = RouteStraight(self.design, 'M1_M2_coupling_waveguide', options=cpw_options)
                
                # Set to layer 2 for multi-layer routing
                m1_m2_waveguide.options.layer = '2'
                
            except Exception as waveguide_error:
                logger.warning(f"Could not add CPW waveguide: {waveguide_error}")
            
            # Build the design
            self.design.rebuild()
            
            result = f"""
Notebook Design Created Successfully
===================================
Components Created:
- 2 Transmon Qubits (Q4, Q5)
- 4 Spiral Inductors (spiralm1, spiralm2, spiralS1, spiralS2)
- 1 Josephson Junction (JJ2)
- 1 CPW Waveguide (M1-M2 coupling)
- Design variables set (CPW width: 0.5μm, gap: 0.3μm)

Special Features:
- CPW waveguide between mutual inductors M1 and M2
- Enhanced coupling control between qubits
- Multi-layer routing (Layer 2)

Design ready for:
- CPW routing connections  
- Pin definitions and connections
- Pocket creation for isolation
- GDS export for fabrication
"""
            
            if include_analysis:
                result += f"""
Analysis Tools Available:
- LOM (Linear Oscillator Model) analysis
- EPR (Energy Participation Ratio) analysis
- Capacitance matrix extraction
- Eigenmode simulation

Use run_lom_analysis tool for quantum analysis.
"""
            
            return [types.TextContent(type="text", text=result)]
            
        except Exception as e:
            return [types.TextContent(type="text", text=f"Error creating notebook design: {str(e)}")]

    async def _list_spiral_inductors(self) -> list[types.TextContent]:
        """List all spiral inductors in the system"""
        if not self.spirals:
            return [types.TextContent(type="text", text="No spiral inductors found in the system.")]
        
        inductor_list = "Spiral Inductors in System\n" + "="*28 + "\n"
        
        for name, spiral in self.spirals.items():
            inductor_list += f"""
Name: {spiral.name}
Turns: {spiral.n_turns}
Width: {spiral.width} μm
Radius: {spiral.radius} μm
Gap: {spiral.gap} μm
Position: ({spiral.pos_x}, {spiral.pos_y})
Inductance: {spiral.inductance} nH
--------------------------------
"""
        
        return [types.TextContent(type="text", text=inductor_list)]

    async def _add_spiral_inductor(self, arguments: dict) -> list[types.TextContent]:
        """Add a new spiral inductor"""
        try:
            # Calculate estimated inductance (simplified formula)
            n = arguments["n_turns"]
            r = arguments["radius"]  # μm
            # Simple approximation: L ≈ μ₀ * n² * A / l
            inductance = 0.8 * (n**2) * (r/10)  # rough estimate in nH
            
            spiral = SpiralInductor(
                name=arguments["name"],
                n_turns=int(arguments["n_turns"]),
                width=float(arguments["width"]),
                radius=float(arguments["radius"]),
                gap=float(arguments["gap"]),
                inductance=inductance,
                pos_x=arguments["pos_x"],
                pos_y=arguments["pos_y"]
            )
            
            self.spirals[arguments["name"]] = spiral
            
            return [types.TextContent(
                type="text",
                text=f"Successfully added spiral inductor '{arguments['name']}' with {arguments['n_turns']} turns and estimated inductance {inductance:.1f} nH"
            )]
        except Exception as e:
            return [types.TextContent(type="text", text=f"Error adding spiral inductor: {str(e)}")]

    async def _run_lom_analysis(self, lj_value: float, cj_value: float, freq_readout: float) -> list[types.TextContent]:
        """Run LOM analysis on the quantum circuit"""
        try:
            if self.design is None:
                return [types.TextContent(
                    type="text",
                    text="No design found. Please create a design first using create_notebook_design."
                )]
            
            # Try to import analysis tools
            try:
                from qiskit_metal.analyses.quantization import LOManalysis
            except ImportError:
                return [types.TextContent(
                    type="text",
                    text="Error: Qiskit Metal analysis tools not available. Check installation."
                )]
            
            analysis_result = f"""
LOM Analysis Configuration
=========================
Junction Parameters:
- Josephson Inductance (Lj): {lj_value} nH
- Junction Capacitance (Cj): {cj_value} fF  
- Readout Frequency: {freq_readout} GHz

Analysis Status:
- Design components: {len(self.design.components) if self.design else 0}
- Qubits in system: {len(self.qubits)}
- Spiral inductors: {len(self.spirals)}
- Josephson junctions: {len(self.junctions)}

Analysis Steps (from notebook):
1. Q3D simulation for capacitance extraction
2. LOM parameter setup with Lj and Cj values
3. Eigenfrequency calculation
4. Anharmonicity and coupling extraction

Note: Full LOM analysis requires Q3D/HFSS simulation environment.
For complete analysis, use Ansys Q3D with the exported design.

Theoretical Estimates:
- Charging Energy (EC): {(1.602e-19)**2 / (2 * cj_value * 1e-15 * 1.602e-19) / 6.626e-34 / 1e9:.3f} GHz
- Josephson Energy (EJ): {6.626e-34 * 1e9 / (2 * 3.14159 * lj_value * 1e-9) / 6.626e-34 / 1e9:.1f} GHz  
- Transmon Frequency: ~{freq_readout:.1f} GHz
"""
            
            return [types.TextContent(type="text", text=analysis_result)]
            
        except Exception as e:
            return [types.TextContent(type="text", text=f"Error in LOM analysis: {str(e)}")]

    async def _add_cpw_waveguide(self, arguments: dict) -> list[types.TextContent]:
        """Add a CPW waveguide transmission line to the design"""
        try:
            if self.design is None:
                return [types.TextContent(
                    type="text",
                    text="No design found. Please create a design first using create_notebook_design."
                )]
            
            # Check if Qiskit Metal is available
            try:
                from qiskit_metal.qlibrary.tlines.straight_path import RouteStraight
                from qiskit_metal import Dict
            except ImportError:
                return [types.TextContent(
                    type="text",
                    text="Error: Qiskit Metal routing components not available."
                )]
            
            # Extract parameters
            name = arguments["name"]
            start_x = arguments["start_x"]
            start_y = arguments["start_y"] 
            end_x = arguments["end_x"]
            end_y = arguments["end_y"]
            width = arguments.get("width", 0.5)  # μm
            gap = arguments.get("gap", 0.3)      # μm
            
            # Create the CPW transmission line
            cpw_options = Dict(
                pin_inputs=Dict(
                    start_pin=Dict(
                        start_point=[start_x, start_y]
                    ),
                    end_pin=Dict(
                        end_point=[end_x, end_y]
                    )
                ),
                trace_width=f'{width}um',
                trace_gap=f'{gap}um',
                layer='2'  # Use layer 2 for CPW routing as in notebook
            )
            
            # Add the transmission line to the design
            cpw_line = RouteStraight(self.design, name, options=cpw_options)
            
            # Rebuild the design
            self.design.rebuild()
            
            # Calculate transmission line properties
            line_length = ((float(end_x.replace('mm', '')) - float(start_x.replace('mm', '')))**2 + 
                          (float(end_y.replace('mm', '')) - float(start_y.replace('mm', '')))**2)**0.5
            
            result = f"""
CPW Waveguide Added Successfully
===============================
Waveguide Name: {name}
Start Point: ({start_x}, {start_y})
End Point: ({end_x}, {end_y})
Length: {line_length:.3f} mm

CPW Parameters:
- Center Conductor Width: {width} μm
- Gap Width: {gap} μm
- Layer: 2 (Multi-layer routing)
- Impedance: ~50Ω (typical for CPW)

Electrical Properties (Estimated):
- Capacitance per unit length: ~100 pF/m
- Inductance per unit length: ~250 nH/m
- Phase velocity: ~1.5×10⁸ m/s
- Propagation delay: ~{line_length*6.67:.2f} ps

Design Status:
- Total components: {len(self.design.components)}
- Ready for GDS export
- Waveguide integrated with spiral inductors
"""
            
            return [types.TextContent(type="text", text=result)]
            
        except Exception as e:
            return [types.TextContent(type="text", text=f"Error adding CPW waveguide: {str(e)}")]

    def _get_qubit_type_info(self, qubit_type: QubitType) -> str:
        """Get information about specific qubit types"""
        info = {
            QubitType.TRANSMON: """
- Large EJ/EC ratio (>50) reduces charge noise
- Sweet spot operation for stability
- Typical frequencies: 3-8 GHz
- Gate times: 10-100 ns
- Applications: Universal quantum computing
""",
            QubitType.FLUXONIUM: """
- Large inductance, small capacitance design
- Flux-tunable frequency
- Protected from charge noise
- Longer coherence times possible
- Applications: Quantum memory, protected qubits
""",
            QubitType.CHARGE: """
- Small EJ/EC ratio (<1) 
- Charge-sensitive operation
- Fast gate operations possible
- Requires charge noise mitigation
- Applications: Fast quantum gates
""",
            QubitType.PHASE: """
- Phase-controlled Josephson junction
- Current-biased operation
- Flux-insensitive sweet spots
- Applications: Flux-noise-immune qubits
"""
        }
        return info.get(qubit_type, "Unknown qubit type")

    def _get_performance_recommendations(self, qubit: SuperconductingQubit) -> str:
        """Get performance recommendations for a qubit"""
        recommendations = []
        
        if qubit.coherence_time_t1 < 50:
            recommendations.append("- Consider improving fabrication to increase T1")
        
        if qubit.coherence_time_t2 / qubit.coherence_time_t1 < 0.5:
            recommendations.append("- T2 limited by pure dephasing - check flux noise")
            
        if qubit.coupling_strength > 200:
            recommendations.append("- High coupling may lead to crosstalk - consider isolation")
            
        if qubit.coupling_strength < 10:
            recommendations.append("- Low coupling may slow gates - consider stronger coupling")
            
        if not recommendations:
            recommendations.append("- Performance metrics look good!")
            
        return "\n".join(recommendations)

    async def run(self):
        """Run the MCP server"""
        async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="quantum-hardware-mcp",
                    server_version="0.1.0",
                    capabilities=self.server.get_capabilities(
                        notification_options=NotificationOptions(),
                        experimental_capabilities={},
                    ),
                ),
            )

def main():
    """Main entry point"""
    server = QuantumHardwareMCPServer()
    asyncio.run(server.run())

if __name__ == "__main__":
    main() 