# === Imports and Globals ===
import mcp
from mcp.types import TextContent
from qiskit_metal import Dict, designs, MetalGUI
from qiskit_metal.qlibrary.sample_shapes.n_square_spiral import NSquareSpiral
from qiskit_metal.qlibrary.qubits.transmon_pocket import TransmonPocket
from qiskit_metal.qlibrary.qubits.JJ_Manhattan import jj_manhattan
from qiskit_metal.qlibrary.tlines.straight_path import RouteStraight
from qiskit_metal.qlibrary.terminations.open_to_ground import OpenToGround
import numpy as np

# Global holders for stateful objects
design = None
gui = None

# === Tool 1: Create Design ===
@mcp.tool()
def create_design() -> TextContent:
    """Initialize the Qiskit Metal planar design and GUI."""
    global design, gui
    design = designs.DesignPlanar()
    design.overwrite_enabled = True
    gui = MetalGUI(design)
    return TextContent(type="text", text="Design and GUI initialized successfully.")

# === Tool 2: Set Design Variables ===
@mcp.tool()
def set_design_variables() -> TextContent:
    """Set basic design variables like CPW width and gap."""
    global design
    if design is None:
        return TextContent(type="text", text="Please run create_design() first.")
    
    design.variables['cpw_width'] = '0.5um'
    design.variables['cpw_gap'] = '0.3um'
    return TextContent(type="text", text="Design variables set: cpw_width=0.5um, cpw_gap=0.3um.")

# === Tool 3: Create Transmon Qubits ===
@mcp.tool()
def create_transmons() -> TextContent:
    """Add transmon pockets Q1 and Q2 to the design."""
    global design
    if design is None:
        return TextContent(type="text", text="Please run create_design() first.")

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

    return TextContent(type="text", text="Transmon Q1 and Q2 added to design.")

# === Tool 4: Add Coupler (NSquareSpiral) ===
@mcp.tool()
def add_coupler() -> TextContent:
    """Add a square spiral coupler between Q1 and Q2."""
    global design
    if design is None:
        return TextContent(type="text", text="Please run create_design() first.")

    NSquareSpiral(design, 'SpiralCoupler', options=dict(
        n=3,
        spacing='0.2mm',
        width='0.02mm',
        orientation='0',
        pos_x='0mm',
        pos_y='0mm'
    ))

    return TextContent(type="text", text="Square spiral coupler added.")

# === Tool 5: Add Josephson Junction ===
@mcp.tool()
def add_josephson_junction() -> TextContent:
    """Add a Josephson junction using the Manhattan model."""
    global design
    if design is None:
        return TextContent(type="text", text="Please run create_design() first.")

    jj_manhattan(design, 'JJ1', options=dict(
        width='0.01mm',
        orientation='90',
        pos_x='0mm',
        pos_y='0mm'
    ))

    return TextContent(type="text", text="Josephson Junction JJ1 added.")

# === Tool 6: Add Transmission Line and Termination ===
@mcp.tool()
def add_tlines_and_termination() -> TextContent:
    """Add a CPW straight path and open-to-ground termination."""
    global design
    if design is None:
        return TextContent(type="text", text="Please run create_design() first.")

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

    return TextContent(type="text", text="Transmission line and termination added.")

# === Tool 7: Export Design to GDS ===
@mcp.tool()
def export_design_to_gds() -> TextContent:
    """Export the current design to a GDS file."""
    global design
    if design is None:
        return TextContent(type="text", text="Please run create_design() first.")

    a_gds = design.renderers.gds

    a_gds.options['path_filename'] = 'C:\\Users\\actc\\Desktop\\University\\Masters\\seminar\\solving simulating problems\\Fake_Junctions.GDS'
    a_gds.options['check_short_segments_by_scaling_fillet'] = 2.0
    a_gds.options['short_segments_to_not_fillet'] = 'True'

    export_path = 'C:\\Users\\actc\\Desktop\\University\\Masters\\seminar\\solving simulating problems\\GDS QRenderer Notebook.gds'
    a_gds.export_to_gds(export_path)

    return TextContent(type="text", text=f"Design successfully exported to GDS at: {export_path}")
