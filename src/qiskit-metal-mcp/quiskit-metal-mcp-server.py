#!/usr/bin/env python3

# === Imports ===
import os
from fastmcp import FastMCP

# Try to import qiskit-metal components, but make them optional
try:
    from qiskit_metal import Dict as QDict, designs, MetalGUI
    from qiskit_metal.qlibrary.sample_shapes.n_square_spiral import NSquareSpiral
    from qiskit_metal.qlibrary.qubits.transmon_pocket import TransmonPocket
    from qiskit_metal.qlibrary.qubits.JJ_Manhattan import jj_manhattan
    from qiskit_metal.qlibrary.tlines.straight_path import RouteStraight
    from qiskit_metal.qlibrary.terminations.open_to_ground import OpenToGround
    import numpy as np
    QISKIT_METAL_AVAILABLE = True
    print("✓ Qiskit Metal imported successfully")
except ImportError as e:
    print(f"⚠ Warning: Qiskit Metal not available: {e}")
    QISKIT_METAL_AVAILABLE = False
    # Create dummy classes for graceful degradation
    class DummyClass:
        def __init__(self, *args, **kwargs):
            pass
    designs = type('', (), {'DesignPlanar': DummyClass})()
    TransmonPocket = jj_manhattan = NSquareSpiral = RouteStraight = OpenToGround = DummyClass

# Initialize FastMCP
mcp = FastMCP("Qiskit Metal MCP Server")

# Global holders for stateful objects
design = None
gui = None

# === Tool 1: Create Design ===
@mcp.tool()
def create_design() -> str:
    """Initialize the Qiskit Metal planar design and GUI."""
    global design, gui
    
    if not QISKIT_METAL_AVAILABLE:
        return "❌ Error: Qiskit Metal is not available. Please install qiskit-metal and its dependencies."
    
    try:
        design = designs.DesignPlanar()
        design.overwrite_enabled = True
        # Skip GUI in headless environments
        # gui = MetalGUI(design)
        return "✓ Design initialized successfully."
    except Exception as e:
        return f"❌ Error creating design: {str(e)}"

# === Tool 2: Set Design Variables ===
@mcp.tool()
def set_design_variables() -> str:
    """Set basic design variables like CPW width and gap."""
    global design
    
    if not QISKIT_METAL_AVAILABLE:
        return "❌ Error: Qiskit Metal is not available."
        
    if design is None:
        return "❌ Please run create_design() first."
    
    try:
        design.variables['cpw_width'] = '0.5um'
        design.variables['cpw_gap'] = '0.3um'
        return "✓ Design variables set: cpw_width=0.5um, cpw_gap=0.3um."
    except Exception as e:
        return f"❌ Error setting variables: {str(e)}"

# === Tool 3: Create Transmon Qubits ===
@mcp.tool()
def create_transmons() -> str:
    """Add transmon pockets Q1 and Q2 to the design."""
    global design
    
    if not QISKIT_METAL_AVAILABLE:
        return "❌ Error: Qiskit Metal is not available."
        
    if design is None:
        return "❌ Please run create_design() first."

    try:
        TransmonPocket(design, 'Q1', options=dict(
            pad_width='425um',
            pad_height='250um',
            pocket_width='650um',
            pocket_height='450um',
            connection_pads=dict(
                a=dict(loc_W=+1, loc_H=0),
                b=dict(loc_W=-1, loc_H=0)
            ),
            pos_x='-2.5mm',
            pos_y='0mm'
        ))

        TransmonPocket(design, 'Q2', options=dict(
            pad_width='425um',
            pad_height='250um',
            pocket_width='650um',
            pocket_height='450um',
            connection_pads=dict(
                a=dict(loc_W=+1, loc_H=0),
                b=dict(loc_W=-1, loc_H=0)
            ),
            pos_x='+2.5mm',
            pos_y='0mm'
        ))

        return "✓ Transmon Q1 and Q2 added to design."
    except Exception as e:
        return f"❌ Error creating transmons: {str(e)}"

# === Tool 4: Add Coupler (NSquareSpiral) ===
@mcp.tool()
def add_coupler() -> str:
    """Add a square spiral coupler between Q1 and Q2."""
    global design
    
    if not QISKIT_METAL_AVAILABLE:
        return "❌ Error: Qiskit Metal is not available."
        
    if design is None:
        return "❌ Please run create_design() first."

    try:
        NSquareSpiral(design, 'SpiralCoupler', options=dict(
            n=3,
            spacing='0.2mm',
            width='0.02mm',
            orientation='0',
            pos_x='0mm',
            pos_y='0mm'
        ))

        return "✓ Square spiral coupler added."
    except Exception as e:
        return f"❌ Error adding coupler: {str(e)}"

# === Tool 5: Add Josephson Junction ===
@mcp.tool()
def add_josephson_junction() -> str:
    """Add a Josephson junction using the Manhattan model."""
    global design
    
    if not QISKIT_METAL_AVAILABLE:
        return "❌ Error: Qiskit Metal is not available."
        
    if design is None:
        return "❌ Please run create_design() first."

    try:
        jj_manhattan(design, 'JJ1', options=dict(
            width='0.01mm',
            orientation='90',
            pos_x='0mm',
            pos_y='0mm'
        ))

        return "✓ Josephson Junction JJ1 added."
    except Exception as e:
        return f"❌ Error adding junction: {str(e)}"

# === Tool 6: Add Transmission Line and Termination ===
@mcp.tool()
def add_tlines_and_termination() -> str:
    """Add a CPW straight path and open-to-ground termination."""
    global design
    
    if not QISKIT_METAL_AVAILABLE:
        return "❌ Error: Qiskit Metal is not available."
        
    if design is None:
        return "❌ Please run create_design() first."

    try:
        RouteStraight(design, 'CPW_Line', options=dict(
            pin_inputs=dict(
                start_pin=('Q1', 'a'),
                end_pin=('Q2', 'b')
            ),
            fillet='50um'
        ))

        OpenToGround(design, 'Term1', options=dict(
            pin_inputs=dict(start_pin=('Q1', 'b'))
        ))

        return "✓ Transmission line and termination added."
    except Exception as e:
        return f"❌ Error adding transmission line: {str(e)}"

# === Tool 7: Export Design to GDS ===
@mcp.tool()
def export_design_to_gds(export_path: str = "./quantum_design.gds") -> str:
    """Export the current design to a GDS file."""
    global design
    
    if not QISKIT_METAL_AVAILABLE:
        return "❌ Error: Qiskit Metal is not available."
        
    if design is None:
        return "❌ Please run create_design() first."

    try:
        a_gds = design.renderers.gds
        
        # Use cross-platform paths
        abs_export_path = os.path.abspath(export_path)
        
        a_gds.options['check_short_segments_by_scaling_fillet'] = 2.0
        a_gds.options['short_segments_to_not_fillet'] = 'True'

        a_gds.export_to_gds(abs_export_path)

        return f"✓ Design successfully exported to GDS at: {abs_export_path}"
    except Exception as e:
        return f"❌ Error exporting to GDS: {str(e)}"

# === Tool 8: Get Design Info ===
@mcp.tool()
def get_design_info() -> str:
    """Get information about the current design."""
    global design
    
    if not QISKIT_METAL_AVAILABLE:
        return "❌ Error: Qiskit Metal is not available."
        
    if design is None:
        return "❌ No design created yet. Please run create_design() first."
    
    try:
        components = list(design.components.keys())
        variables = dict(design.variables)
        
        info = f"""
✓ Current Design Information:
========================
Components: {', '.join(components) if components else 'None'}
Variables: {variables}
Design Name: {design.name}
Design Class: {design.__class__.__name__}
        """
        return info.strip()
    except Exception as e:
        return f"❌ Error getting design info: {str(e)}"

# === Tool 9: Clear Design ===
@mcp.tool()
def clear_design() -> str:
    """Clear the current design and start fresh."""
    global design, gui
    try:
        design = None
        gui = None
        return "✓ Design cleared successfully."
    except Exception as e:
        return f"❌ Error clearing design: {str(e)}"

# === Tool 10: Check Status ===
@mcp.tool()
def check_status() -> str:
    """Check the status of Qiskit Metal and the current design."""
    status = f"""
🔍 Qiskit Metal MCP Server Status:
================================
Qiskit Metal Available: {'✓ Yes' if QISKIT_METAL_AVAILABLE else '❌ No'}
Current Design: {'✓ Created' if design is not None else '❌ Not created'}
"""
    if design is not None:
        try:
            components = list(design.components.keys())
            status += f"Components: {len(components)} ({', '.join(components) if components else 'None'})\n"
        except:
            status += "Components: Error reading\n"
    
    return status.strip()

if __name__ == "__main__":
    print("🚀 Starting Qiskit Metal FastMCP Server...")
    print(f"📊 Qiskit Metal Available: {QISKIT_METAL_AVAILABLE}")
    mcp.run()
