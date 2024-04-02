""" Script to generate the Gibson Rooms dataset from the Gibson dataset. 

Gibson Rooms is created by splitting the original Gibson meshes into rooms based on the bounding box
information provided in the 3DSceneGraphs dataset. The script reads the mesh and bounding box information
from the Gibson and 3DSceneGraphs datasets, respectively, and saves the meshes of individual rooms and
corresponding metadata in a new directory.
"""
import argparse
import glob
import json
import os

import numpy as np
import trimesh
from tqdm import tqdm


def mesh2points(mesh_path, save_path, num_points=10000):
    """
    Converts a 3D mesh to a point cloud by sampling points uniformly on the mesh surface
    and saves the point cloud to a .npz file.

    Args:
        obj_path (str): path to the .obj file of the mesh.
        num_points (int): number of points to sample on the mesh surface.
    """
    # Load the mesh
    mesh = trimesh.load(mesh_path)

    # Sample points on the mesh surface
    cloud = trimesh.points.PointCloud(mesh.sample(num_points))

    # Save the point cloud to a .npz file
    np.savez(save_path, points=cloud.vertices)


def numpy2json(arr):
    """ Recursively converts numpy arrays to JSON-serializable objects. """
    if isinstance(arr, dict):
        return {k: numpy2json(v) for k, v in arr.items()}
    elif isinstance(arr, list):
        return [numpy2json(element) for element in arr]
    elif isinstance(arr, np.ndarray):
        return arr.tolist()
    else:
        return arr


def load_graph(graph_path):
    a = np.load(graph_path, allow_pickle=True)
    return numpy2json(a['output'].item())


def split_building_mesh(mesh, bbox_center, bbox_size):
    """
    Creates a new mesh from the original mesh based on the center and size of a bounding box.

    Args:
        mesh (trimesh.Trimesh): The original building mesh from Gibson dataset.
        bbox_center (tuple): The center coordinates (x, y, z) of the bounding box.
        bbox_size (tupe): The size (length, width, height) of the bounding box.

    Returns:
        trimesh.Trimesh: The mesh of the room extracted from the original mesh.
    """
    # Calculate bbox_min and bbox_max from bbox_center and bbox_size
    bbox_min = np.array(bbox_center) - np.array(bbox_size) / 2
    bbox_max = np.array(bbox_center) + np.array(bbox_size) / 2

    # Find vertices within the bounding box
    inside_bbox = np.all((mesh.vertices >= bbox_min) &
                         (mesh.vertices <= bbox_max), axis=1)
    # Get the indices of vertices inside the bbox
    inside_vertex_indices = np.where(inside_bbox)[0]

    # Create a mapping from old vertex indices to new ones
    new_vertex_indices = {old_index: new_index for new_index,
                          old_index in enumerate(inside_vertex_indices)}

    # Filter faces to only those where all vertices are inside the bbox, and update their indices
    filtered_faces = []
    for face in mesh.faces:
        if all(vertex in inside_vertex_indices for vertex in face):
            # Update face indices to correspond to the new vertex indices
            new_face = [new_vertex_indices[vertex] for vertex in face]
            filtered_faces.append(new_face)

    # Create new mesh using filtered vertices and faces
    new_mesh = trimesh.Trimesh(
        vertices=mesh.vertices[inside_bbox], faces=filtered_faces)
    return new_mesh


def split_building_graph(graph, room_id):
    """
    Extracts the objects in a room from the 3DSceneGraph data and returns them as a dictionary.

    Args:
        graph (dict): The scene graph data loaded from the .npz file.
        room_id (int): The ID of the room whose objects are to be extracted.

    Returns:
        dict: A dictionary containing the information of the room and the objects in it.
    """
    return {
        'building': graph['building'],
        'room': graph['room'][room_id],
        'object': [o for o in graph['object'].values() if o['parent_room'] == room_id]
    }


def split_building(mesh_path, graph_path, output_dir):
    """
    Splits a building mesh into rooms based on the bounding box information provided in
    the corresponding 3DSceneGraph file and saves the meshes of individual rooms and
    corresponding metadata in a new directory.
    """
    # Load the mesh
    mesh = trimesh.load(mesh_path)

    # Load the scene graph
    graph = load_graph(graph_path)

    # Create output directory
    mesh_name = mesh_path.split('/')[-2]
    output_dir = os.path.join(output_dir, mesh_name)
    os.makedirs(output_dir, exist_ok=True)

    for room_id in tqdm(list(graph['room'].keys()), desc=f'Processing {mesh_name}'):
        # Get room information
        room_graph = split_building_graph(graph, room_id)

        # Locate the center point and size of the room
        center = room_graph['room']['location']   # Center Point
        size = room_graph['room']['size']    # Length, width, height

        # Segment the room mesh
        room_mesh = split_building_mesh(mesh, center, size)

        # Create an output directory for the room
        room_dir = os.path.join(output_dir, f'room_{str(room_id)}')
        os.makedirs(room_dir, exist_ok=True)

        # Save the room mesh and metadata
        room_mesh.export(os.path.join(room_dir, 'mesh.obj'))
        with open(os.path.join(room_dir, 'metadata.json'), 'w') as f:
            json.dump(room_graph, f)

        # Convert mesh to point cloud and save it
        mesh2points(os.path.join(room_dir, 'mesh.obj'),
                    os.path.join(room_dir, 'points.npz'))

if __name__ == '__main__':
    # Parse command line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('--mode', choices=['tiny', 'medium'], default='tiny',
                        help='Mode of the Gibson dataset (tiny, medium).')
    parser.add_argument('--graph_type', choices=['automated', 'verified'], default='verified',
                        help='Type of the 3DSceneGraph dataset (automated, verified). Verified graphs \
                            are only available for the tiny dataset.')
    parser.add_argument('--gibson_path', type=str, default='data/gibson/raw/',
                        help='Path to the Gibson dataset.')
    parser.add_argument('--output_path', type=str, default='data/gibson/raw/',
                        help='Path to save the Gibson Rooms dataset.')
    args = parser.parse_args()

    # Read command line arguments
    mode = args.mode
    graph_type = args.graph_type
    if mode == 'medium' and graph_type == 'verified':
        raise ValueError(
            'Verified graphs are only available for the tiny dataset.')

    # Find all building meshes in the Gibson dataset
    buildings_path = os.path.join(args.gibson_path, f'gibson_{mode}/')
    buildings = glob.glob(f'{buildings_path}*/mesh_z_up.obj')

    # Create output directories
    gibson_rooms_path = os.path.join(args.output_path, f'gibson_{mode}_rooms')
    os.makedirs(gibson_rooms_path, exist_ok=True)

    # Split meshes into rooms and save them
    scene_graphs_path = os.path.join(args.gibson_path, f'gibson_{mode}_graphs/{graph_type}_graph/3DSceneGraph_')
    for i, mesh_path in enumerate(sorted(buildings)):
        graph_path = mesh_path.replace(buildings_path, scene_graphs_path)
        graph_path = graph_path.replace('/mesh_z_up.obj', '.npz')
        if not os.path.exists(graph_path):
            raise FileNotFoundError(f'Graph file not found: {graph_path}')

        split_building(mesh_path, graph_path, gibson_rooms_path)