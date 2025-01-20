import trimesh
import numpy as np


def visualize_building_with_room_mask(obj_path, point, size):
    """
    Visualizes a 3D mesh with a bounding box centered at a given point.

    Parameters:
    - obj_path: str, path to the .obj file of the mesh.
    - point: array-like, 3D coordinates of the point where the bbox is centered (x, y, z).
    - size: array-like, size of the bbox (length, width, height).
    """
    # Load the 3D mesh
    mesh = trimesh.load(obj_path)

    # Calculate the center of the bbox from the corner point
    # center_point = np.array(point) - np.array(size) / 2
    center_point = np.array(point)

    # Create the bbox
    bbox = trimesh.creation.box(
        extents=size, transform=trimesh.transformations.translation_matrix(center_point))

    # Create a scene and add both the mesh and the bbox for visualization
    scene = trimesh.Scene([mesh, bbox])

    # Visualize the scene
    scene.show()


def visualize_building_room(obj_path, bbox_center, bbox_size):
    """
    Creates a new mesh from the original mesh based on the center and size of a bounding box.

    Parameters:
    - original_mesh: A trimesh.Trimesh object of the original mesh.
    - bbox_center: The center coordinates (x, y, z) of the bounding box.
    - bbox_size: The size (length, width, height) of the bounding box.

    Returns:
    - A trimesh.Trimesh object of the mesh within the specified bounding box.
    """
    original_mesh = trimesh.load(obj_path)
    # Calculate bbox_min and bbox_max from bbox_center and bbox_size
    bbox_min = np.array(bbox_center) - np.array(bbox_size) / 2
    bbox_max = np.array(bbox_center) + np.array(bbox_size) / 2

    # Find vertices within the bounding box
    inside_bbox = np.all((original_mesh.vertices >= bbox_min) & (
        original_mesh.vertices <= bbox_max), axis=1)
    # Get the indices of vertices inside the bbox
    inside_vertex_indices = np.where(inside_bbox)[0]

    # Create a mapping from old vertex indices to new ones
    new_vertex_indices = {old_index: new_index for new_index,
                          old_index in enumerate(inside_vertex_indices)}

    # Filter faces to only those where all vertices are inside the bbox, and update their indices
    filtered_faces = []
    for face in original_mesh.faces:
        if all(vertex in inside_vertex_indices for vertex in face):
            # Update face indices to correspond to the new vertex indices
            new_face = [new_vertex_indices[vertex] for vertex in face]
            filtered_faces.append(new_face)

    # Create new mesh using filtered vertices and faces
    new_mesh = trimesh.Trimesh(
        vertices=original_mesh.vertices[inside_bbox], faces=filtered_faces)

    # Visualize the new mesh
    scene = trimesh.Scene([new_mesh])
    scene.show()


if __name__ == '__main__':
    # Define paths.
    scene_name = "Allensville"
    graph_path = "3DSceneGraph_tiny/data/verified_graph/3DSceneGraph_${scene_name}.npz"
    mesh_path = "gibson_tiny/${scene_name}/mesh_z_up.obj"

    # Load room data from the graph.
    room_id = 1
    room_data = np.load(graph_path, allow_pickle=True)['output'].item()
    center = room_data['room'][room_id]['location']
    size = room_data['room'][room_id]['size']

    # Visualize the building with the room mask.
    visualize_building_with_room_mask(mesh_path, center, size)

    # Visualize the room only.
    visualize_building_room(mesh_path, center, size)
