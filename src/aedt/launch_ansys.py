from pyaedt import Q3d, Desktop

# Launch AEDT and start Q3D in graphical mode
desktop = Desktop(specified_version="2024.2", non_graphical=False, new_desktop=True)
q3d = Q3d(projectname="GDS_Q3D_CapExtract", designname="CapacitanceExtract", solution_type="Electrostatic")

# Import the GDS file
gds_path = r"C:\Path\To\Your\File.gds"  # <-- Replace with your GDS file path
q3d.import_gds(gds_path)

# Assign nets automatically based on imported objects
all_objects = q3d.modeler.object_names
print(f"Imported objects: {all_objects}")

for i, obj_name in enumerate(all_objects):
    faces = q3d.modeler.get_face_ids(obj_name)
    if faces:
        net_name = f"Net{i+1}"
        q3d.assign_net_to_faces(net_name, faces)
        print(f"Assigned {net_name} to faces of {obj_name}")

# Create and update simulation setup
setup = q3d.create_setup("Setup1")
setup.props["MaximumPasses"] = 10
setup.props["MinimumPasses"] = 2
setup.props["MinimumConvergedPasses"] = 2
setup.update()

# Run the analysis
q3d.analyze()

# Extract capacitance matrix (in Farads)
cap_matrix = q3d.get_capacitance_matrix()

print("\nCapacitance Matrix (Farads):")
for row in cap_matrix:
    print(row)

# Optionally save project
q3d.save_project()

# Close AEDT session
q3d.release_desktop(close_projects=True, close_desktop=True)