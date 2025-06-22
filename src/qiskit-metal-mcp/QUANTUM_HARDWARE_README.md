# Quantum Hardware MCP Server

## Based on BZU Quantum Computing Hardware Notebook

This Model Context Protocol (MCP) server provides comprehensive tools for managing quantum computing hardware, specifically designed around the concepts and technologies presented in the BZU Quantum Computing Hardware Team's Jupyter notebook.

## 🎯 Overview

The server implements functionality for:
- **Superconducting Qubits**: Management and analysis of transmon, fluxonium, charge, and phase qubits
- **Josephson Junctions**: Physical parameter analysis and current-voltage characteristics  
- **Qiskit Metal Integration**: Installation management and environment setup
- **Circuit Design**: Automated parameter calculation for quantum circuits
- **Performance Metrics**: Coherence time analysis and gate fidelity calculations

## 🚀 Features

### Core Quantum Hardware Management
- ✅ Qubit information database with coherence times, frequencies, and coupling strengths
- ✅ Josephson junction analysis with energy scale calculations
- ✅ Performance metrics calculation (T1, T2, gate fidelities)
- ✅ Circuit design parameter generation

### Qiskit Metal Integration  
- ✅ Automated dependency checking (qiskit-metal, pyside2, geopandas, jupyter)
- ✅ Installation management with conda environment support
- ✅ Environment setup verification

### Circuit Design Tools
- ✅ Transmon qubit design parameters
- ✅ CPW resonator design calculations
- ✅ Tunable coupler specifications
- ✅ Frequency-dependent parameter optimization

## 🛠️ Available Tools

| Tool | Description | Key Parameters |
|------|-------------|----------------|
| `get_hardware_overview` | System architecture overview | None |
| `list_all_qubits` | List all superconducting qubits | None |
| `get_qubit_info` | Detailed qubit information | `qubit_name` |
| `analyze_josephson_junction` | Junction parameter analysis | `junction_name` |
| `calculate_qubit_metrics` | Performance metrics calculation | `qubit_name` |
| `generate_circuit_design` | Circuit design parameters | `circuit_type`, `target_frequency` |
| `add_qubit` | Add new superconducting qubits | `name`, `qubit_type`, `frequency`, etc. |
| `check_qiskit_installation` | Check Qiskit Metal status | None |
| `install_qiskit_dependencies` | Install Qiskit Metal | `force_reinstall` (optional) |

## 📋 Installation & Setup

### Prerequisites
- Python 3.7+
- MCP-compatible client
- Optional: Conda for Qiskit Metal environment

### Configuration

1. **Add to MCP client configuration:**
```json
{
  "mcpServers": {
    "quantum-hardware": {
      "command": "python3",
      "args": ["quantum_hardware_mcp_server.py"],
      "env": {
        "PYTHONPATH": "."
      }
    }
  }
}
```

2. **Run the server directly:**
```bash
python3 quantum_hardware_mcp_server.py
```

3. **Test the installation:**
```bash
python3 test_quantum_hardware.py
```

## 🔬 Example Usage

### Get System Overview
```python
# Get comprehensive hardware overview
result = await mcp_call("get_hardware_overview", {})
```

### Analyze Existing Hardware
```python
# Get information about the pocket transmon
result = await mcp_call("get_qubit_info", {"qubit_name": "transmon_1"})

# Analyze Josephson junction parameters
result = await mcp_call("analyze_josephson_junction", {"junction_name": "junction_1"})
```

### Design New Circuits
```python
# Generate transmon design for 5.5 GHz
result = await mcp_call("generate_circuit_design", {
    "circuit_type": "transmon",
    "target_frequency": 5.5
})

# Design CPW resonator for 7.2 GHz
result = await mcp_call("generate_circuit_design", {
    "circuit_type": "cpw_resonator", 
    "target_frequency": 7.2
})
```

### Add New Hardware
```python
# Add a fluxonium qubit to the system
result = await mcp_call("add_qubit", {
    "name": "flux_qubit_1",
    "qubit_type": "fluxonium",
    "frequency": 0.8,
    "coupling_strength": 25.0,
    "coherence_time_t1": 150.0,
    "coherence_time_t2": 200.0
})
```

### Environment Management
```python
# Check Qiskit Metal installation status
result = await mcp_call("check_qiskit_installation", {})

# Install missing dependencies
result = await mcp_call("install_qiskit_dependencies", {"force_reinstall": false})
```

## 📊 Sample Data

The server comes pre-loaded with sample quantum hardware data:

### Pocket Transmon Qubit
- **Type**: Transmon
- **Frequency**: 5.2 GHz  
- **Coupling Strength**: 50.0 MHz
- **T1 Coherence**: 80.0 μs
- **T2 Coherence**: 60.0 μs

### Josephson Junction
- **Critical Current**: 15.0 nA
- **Capacitance**: 80.0 fF
- **Resistance**: 150.0 Ω
- **Josephson Energy**: 25.0 GHz
- **Charging Energy**: 0.3 GHz

## 🧪 Testing

The test suite demonstrates all functionality:

```bash
python3 test_quantum_hardware.py
```

This will run 9 comprehensive tests covering:
- Hardware overview and qubit listing
- Detailed qubit information and metrics
- Josephson junction analysis  
- Circuit design generation
- Qubit addition and management
- Qiskit Metal installation checking

## 📚 BZU Notebook Integration

This MCP server directly implements concepts from the BZU Quantum Computing Hardware notebook:

### Installation Management
- Mirrors the conda environment setup instructions
- Automates the pip installation process for qiskit-metal, pyside2, geopandas, jupyter
- Provides verification and troubleshooting tools

### Superconducting Qubit Knowledge
- Implements transmon and fluxonium qubit models
- Calculates performance metrics based on coherence times
- Provides design recommendations and optimization guidance

### Josephson Junction Analysis
- Current-voltage relationship modeling
- Energy scale calculations (EJ, EC, EJ/EC ratios)
- Regime identification (transmon vs charge vs intermediate)
- Plasma frequency and anharmonicity calculations

### Circuit Design
- Automated parameter calculation for different circuit types
- Frequency-dependent design optimization
- Physical dimension estimates and coupling calculations

## 🤝 Contributing

The server architecture is modular and extensible. To add new functionality:

1. **Add new qubit types**: Extend the `QubitType` enum and update analysis methods
2. **Add circuit designs**: Extend the `generate_circuit_design` method with new circuit types  
3. **Add analysis tools**: Implement new calculation methods for specific hardware parameters
4. **Add installation tools**: Extend dependency management for additional quantum software packages

## 📄 Files

- `quantum_hardware_mcp_server.py` - Main MCP server implementation
- `quantum_hardware_config.json` - MCP client configuration
- `test_quantum_hardware.py` - Comprehensive test suite
- `QUANTUM_HARDWARE_USAGE.md` - Detailed usage examples
- `_1_hardware,_BZU_QC_.ipynb` - Original BZU notebook (source material)

## 🏗️ Architecture

The server is built using:
- **MCP Protocol**: Standard Model Context Protocol for tool integration
- **Async/Await**: Non-blocking operation support
- **Dataclasses**: Structured quantum hardware representation
- **NumPy**: Scientific calculations for quantum parameters
- **Type Hints**: Full type safety and IDE support

## ⚡ Key Advantages

- **Comprehensive**: Covers all major aspects of superconducting quantum hardware
- **Educational**: Based on established quantum computing curriculum (BZU notebook)
- **Practical**: Provides real design parameters and performance calculations
- **Extensible**: Modular architecture for easy expansion
- **Standards-based**: Uses MCP protocol for broad compatibility

---

*Based on the BZU Quantum Computing Hardware Team notebook, this MCP server brings quantum hardware management capabilities to modern development environments.* 