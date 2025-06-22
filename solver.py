import numpy as np
import gdstk
import argparse

def read_gds(filename, layer_map):
    """
    Reads a GDSII file and extracts polygons for specified layers.

    Args:
        filename (str): Path to the GDSII file.
        layer_map (dict): A dictionary mapping GDS layers {layer: conductor_id}.

    Returns:
        list: A list of tuples, where each tuple contains (polygon_vertices, conductor_id).
    """
    print(f"Reading GDS file: {filename}")
    library = gdstk.read_gds(filename)
    top_cells = library.top_level()
    if not top_cells:
        print("Error: No top-level cells found in GDS file.")
        return []
    top_cell = top_cells[0]

    polygons_with_ids = []
    for poly in top_cell.polygons:
        if poly.layer in layer_map:
            conductor_id = layer_map[poly.layer]
            polygons_with_ids.append((poly.points, conductor_id))

    if not polygons_with_ids:
        print("Warning: No polygons found for the specified layers.")

    return polygons_with_ids

def discretize_polygons(polygons_with_ids, max_segment_length):
    """
    Discretizes polygon boundaries into small segments.

    Args:
        polygons_with_ids (list): A list of tuples (polygon_vertices, conductor_id).
        max_segment_length (float): The maximum length for a segment.

    Returns:
        list: A list of segment dictionaries.
    """
    segments = []
    for poly_verts, conductor_id in polygons_with_ids:
        for i in range(len(poly_verts)):
            p1 = poly_verts[i]
            p2 = poly_verts[(i + 1) % len(poly_verts)]
            
            edge_vector = p2 - p1
            edge_length = np.linalg.norm(edge_vector)
            
            num_segments = int(np.ceil(edge_length / max_segment_length))
            if num_segments == 0:
                continue

            segment_length = edge_length / num_segments
            segment_vector = edge_vector / num_segments

            for j in range(num_segments):
                start_point = p1 + j * segment_vector
                end_point = start_point + segment_vector
                center_point = start_point + 0.5 * segment_vector
                
                segments.append({
                    'start': start_point,
                    'end': end_point,
                    'center': center_point,
                    'length': segment_length,
                    'conductor_id': conductor_id
                })
    return segments

def solve_bem(segments, num_conductors):
    """
    Solves for charge distribution using the Boundary Element Method.

    Args:
        segments (list): A list of segment dictionaries.
        num_conductors (int): The number of conductors.

    Returns:
        np.array: An array of charge densities for each segment, for each conductor simulation.
    """
    n_segments = len(segments)
    if n_segments == 0:
        return np.array([])

    P = np.zeros((n_segments, n_segments))
    epsilon_0 = 8.854187817e-12  # Permittivity of free space in F/m

    # Build the potential influence matrix P
    for i in range(n_segments):
        for j in range(n_segments):
            seg_i = segments[i]
            seg_j = segments[j]
            if i == j:
                # Self-term approximation
                P[i, j] = - (seg_i['length'] / (2 * np.pi * epsilon_0)) * (np.log(seg_i['length'] / 2) - 1)
            else:
                # Off-diagonal term
                dist = np.linalg.norm(seg_i['center'] - seg_j['center'])
                P[i, j] = - (seg_j['length'] / (2 * np.pi * epsilon_0)) * np.log(dist)

    all_sigmas = []
    # Solve for charges by setting each conductor to 1V one at a time
    for k in range(num_conductors):
        V = np.zeros(n_segments)
        for i in range(n_segments):
            if segments[i]['conductor_id'] == k:
                V[i] = 1.0
        
        # Solve for charge densities: P * sigma = V
        sigma = np.linalg.solve(P, V)
        all_sigmas.append(sigma)

    return np.array(all_sigmas)

def calculate_capacitance_matrix(all_sigmas, segments, num_conductors):
    """
    Calculates the capacitance matrix from the charge distribution.

    Args:
        all_sigmas (np.array): Charge densities from each simulation.
        segments (list): List of segment dictionaries.
        num_conductors (int): The number of conductors.

    Returns:
        np.array: The capacitance matrix.
    """
    C = np.zeros((num_conductors, num_conductors))
    for k in range(num_conductors):  # k is the conductor that was held at 1V
        sigma_k = all_sigmas[k]
        for m in range(num_conductors):  # m is the conductor we are calculating the charge on
            Q_m = 0
            for i in range(len(segments)):
                if segments[i]['conductor_id'] == m:
                    Q_m += sigma_k[i] * segments[i]['length']
            C[m, k] = Q_m
    return C

def main():
    """
    Main function to run the electrostatic solver.
    """
    parser = argparse.ArgumentParser(description='2D Electrostatic Capacitance Solver')
    parser.add_argument('gds_file', type=str, help='Path to the GDSII file.')
    parser.add_argument('--layers', type=str, required=True, 
                        help='Layer mapping, e.g., "1:0,2:1" for layer 1 -> cond 0, layer 2 -> cond 1')
    parser.add_argument('--max_seg_len', type=float, default=1.0, 
                        help='Maximum segment length for discretization (in GDS units, e.g., um).')
    
    args = parser.parse_args()

    try:
        layer_map = dict(item.split(':') for item in args.layers.split(','))
        layer_map = {int(k): int(v) for k, v in layer_map.items()}
    except ValueError:
        print("Error: Invalid layer mapping format. Use 'layer:id,layer:id'.")
        return

    print(f"Starting electrostatic simulation for {args.gds_file}")
    print(f"Layers: {layer_map}")
    print(f"Max segment length: {args.max_seg_len} um")


    # 1. Read GDS file to get polygons
    polygons_with_ids = read_gds(args.gds_file, layer_map)
    if not polygons_with_ids:
        print("No polygons found. Exiting.")
        return

    print(f"Found {len(polygons_with_ids)} polygons.")

    # 2. Discretize polygon boundaries
    segments = discretize_polygons(polygons_with_ids, args.max_seg_len)
    if not segments:
        print("No segments generated. Exiting.")
        return
    print(f"Polygons discretized into {len(segments)} segments.")

    # 3. Solve for charge distribution using BEM
    num_conductors = len(layer_map)
    all_sigmas = solve_bem(segments, num_conductors)
    print("BEM solved for charge distribution.")

    # 4. Calculate capacitance matrix
    C = calculate_capacitance_matrix(all_sigmas, segments, num_conductors)
    
    print("\n--- Capacitance Matrix (fF/um) ---")
    # The result is in F/m. Convert to fF/um (1 F/m = 1e-3 fF/um)
    C_femtofarad_per_micron = C * 1e-3
    print(C_femtofarad_per_micron)
    print("------------------------------------")


if __name__ == '__main__':
    main() 