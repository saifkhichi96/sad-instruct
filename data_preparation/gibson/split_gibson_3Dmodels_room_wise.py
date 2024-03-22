import trimesh
import argparse
import json
import numpy as np
import os
from tqdm import tqdm
import glob

def read_npz(npz_path):
    a = np.load(npz_path, allow_pickle=True)
    output_obj = a['output'].item()
    return output_obj

def split_mesh_with_bbox(original_mesh, bbox_center, bbox_size):
    """
    Creates a new mesh from the original mesh based on the center and size of a bounding box.

    Parameters:
    - original_mesh: A trimesh.Trimesh object of the original mesh.
    - bbox_center: The center coordinates (x, y, z) of the bounding box.
    - bbox_size: The size (length, width, height) of the bounding box.

    Returns:
    - A trimesh.Trimesh object of the mesh within the specified bounding box.
    """
    # Calculate bbox_min and bbox_max from bbox_center and bbox_size
    bbox_min = np.array(bbox_center) - np.array(bbox_size) / 2
    bbox_max = np.array(bbox_center) + np.array(bbox_size) / 2

    # Find vertices within the bounding box
    inside_bbox = np.all((original_mesh.vertices >= bbox_min) & (original_mesh.vertices <= bbox_max), axis=1)
    inside_vertex_indices = np.where(inside_bbox)[0]  # Get the indices of vertices inside the bbox
    
    # Create a mapping from old vertex indices to new ones
    new_vertex_indices = {old_index: new_index for new_index, old_index in enumerate(inside_vertex_indices)}
    
    # Filter faces to only those where all vertices are inside the bbox, and update their indices
    filtered_faces = []
    for face in original_mesh.faces:
        if all(vertex in inside_vertex_indices for vertex in face):
            # Update face indices to correspond to the new vertex indices
            new_face = [new_vertex_indices[vertex] for vertex in face]
            filtered_faces.append(new_face)

    # Create new mesh using filtered vertices and faces
    new_mesh = trimesh.Trimesh(vertices=original_mesh.vertices[inside_bbox], faces=filtered_faces)
    return new_mesh


def convert_arrays_to_lists(data):
    if isinstance(data, dict):
        return {k: convert_arrays_to_lists(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [convert_arrays_to_lists(element) for element in data]
    elif isinstance(data, np.ndarray):
        return data.tolist()
    else:
        return data


def save_room_data(mesh_path, npz_path, output_dir):
    mesh = trimesh.load(mesh_path)

    # Load the JSON file
    data=read_npz(npz_path)

    num_rooms=list(data['room'].keys())
    mesh_name=mesh_path.split('/')[-2]
    output_dir=os.path.join(output_dir, mesh_name)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    for room_index in num_rooms:
        # output_dir_base = output_dir
        

        category = data['room'][room_index]['scene_category']
        output_path = os.path.join(output_dir, f'room_{str(room_index)}_{category}_mesh.obj')
        point = data['room'][room_index]['location']   # Center Point
        size = data['room'][room_index]['size']    # Length, width, height
        metadata = data['room'][room_index]
        metadata = convert_arrays_to_lists(metadata)
        with open(os.path.join(output_dir, f'room_{str(room_index)}_{category}_metadata.json'), 'w') as f:
            json.dump(metadata, f)

        room_mesh=split_mesh_with_bbox(mesh, point, size)

        room_mesh.export(output_path)


if __name__ == '__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--datasplit_type', type=str, default='tiny', help='Path to the original mesh file.')
    parser.add_argument('--scene_graphs_type', type=str, default='verified',help='Path to the JSON file containing the bounding box information.')
    # parser.add_argument("--output_dir", type=str, help="Path to the output directory where the split meshes will be saved")


    args=parser.parse_args()

    # save_room_data(args.mesh_path, args.npz_path, args.output_dir)
    # Pattern to match all 'xyz.obj' files within subdirectories of 'a'
    datasplit_type = args.datasplit_type
    scene_graphs_type = args.scene_graphs_type
    scene_graphs_type = 'automated'
    pattern = f'gibson_{datasplit_type}/*/mesh_z_up.obj'
    mesh_base_path = f'gibson_{datasplit_type}/'
    if datasplit_type == 'tiny':
        npz_base_path = f'3DSceneGraph_{datasplit_type}/data/{scene_graphs_type}_graph/3DSceneGraph_'
    elif datasplit_type == 'medium':
        npz_base_path = f'3DSceneGraph_{datasplit_type}/{scene_graphs_type}_graph/3DSceneGraph_'
    # Use glob.glob to find matches
    obj_paths = glob.glob(pattern)

    # Print all found paths
    for mesh_path in tqdm(obj_paths):
        npz_path = mesh_path.replace(mesh_base_path,npz_base_path).replace('/mesh_z_up.obj', '.npz')
        save_room_data(mesh_path,npz_path,f'gibson_{datasplit_type}_roomwise_split_3DModels_{scene_graphs_type}')
    