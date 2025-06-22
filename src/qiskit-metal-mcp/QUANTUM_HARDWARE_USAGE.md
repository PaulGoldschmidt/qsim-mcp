
# Quantum Hardware MCP Server Usage Examples

## Based on BZU Quantum Computing Hardware Notebook

This MCP server provides tools for managing quantum computing hardware,
specifically focused on superconducting qubits and Qiskit Metal integration.

### Available Tools:

1. **get_hardware_overview**: Get system architecture overview
2. **list_all_qubits**: List all superconducting qubits  
3. **get_qubit_info**: Get detailed qubit information
4. **analyze_josephson_junction**: Analyze junction parameters
5. **calculate_qubit_metrics**: Calculate performance metrics
6. **generate_circuit_design**: Generate circuit designs
7. **add_qubit**: Add new qubits to the system
8. **check_qiskit_installation**: Check Qiskit Metal status
9. **install_qiskit_dependencies**: Install Qiskit Metal

### Example Usage:

```python
# Get information about the pocket transmon qubit
result = await mcp_call("get_qubit_info", {"qubit_name": "transmon_1"})

# Analyze the Josephson junction
result = await mcp_call("analyze_josephson_junction", {"junction_name": "junction_1"})

# Generate a transmon design for 5.5 GHz
result = await mcp_call("generate_circuit_design", {
    "circuit_type": "transmon",
    "target_frequency": 5.5
})

# Add a new fluxonium qubit
result = await mcp_call("add_qubit", {
    "name": "flux_qubit_1",
    "qubit_type": "fluxonium", 
    "frequency": 0.8,
    "coupling_strength": 25.0,
    "coherence_time_t1": 150.0,
    "coherence_time_t2": 200.0
})
```

### Integration with BZU Notebook Content:

- **Installation**: Automated Qiskit Metal dependency management
- **Superconducting Qubits**: Transmon and fluxonium support
- **Josephson Junctions**: Current-voltage analysis and energy scales
- **Circuit Design**: Automated parameter calculation
- **Performance Metrics**: Coherence times and gate fidelities

### Configuration:

Add to your MCP client configuration:
```json
{
  "mcpServers": {
    "quantum-hardware": {
      "command": "python",
      "args": ["quantum_hardware_mcp_server.py"]
    }
  }
}
```
