import json
import os


def load_objects(data_dir):
    # Load list of objects
    objects_file = os.path.join(data_dir, 'objects.json')
    with open(objects_file, 'r') as f:
        objects_data = json.load(f)['scans']

    # Index objects
    scan_objects = {s['scan']: s['objects'] for s in objects_data}

    # Define mappings (for faster lookup)
    id2global = {}
    global2label = {}
    for s in objects_data:
        scan_id = s['scan']
        objects = s['objects']

        # Map object id to global id
        id2global[scan_id] = {str(o['id']): str(o['global_id'])
                              for o in objects}

        # Map global id to label
        global2label.update({str(o['global_id']): f"{o['label']}"
                             for o in objects})

    return scan_objects, id2global, global2label


def load_relationships(data_dir, id2global, global2label):
    # Define a list of relations to ignore
    ignore_list = [
        'none',
        'same symmetry as',
        'same as',
        'same object type',
    ]

    # Load relationships data
    relations_file = os.path.join(data_dir, 'relationships.json')
    with open(relations_file, 'r') as f:
        relations_data = json.load(f)['scans']

    scan_relations = {}
    for s in relations_data:
        scan_id = s['scan']

        # Get scan relations
        relations = []
        for rel in s['relationships']:
            # Read relation data (subject, object, relation, relation_name)
            subject_id = str(rel[0])   # subject instance id
            object_id = str(rel[1])    # object instance id
            relation_id = str(rel[2])  # relation id
            relation_name = rel[3]     # relation name

            # Map instance ids to global ids
            subject_id_global = id2global[scan_id][subject_id]
            object_id_global = id2global[scan_id][object_id]

            # Get object names
            subject_name = global2label[subject_id_global]
            object_name = global2label[object_id_global]

            # Skip if relation is in ignore list
            if relation_name in ignore_list:
                continue

            relations.append({
                'subject_id': subject_id_global,
                'subject_name': f"{subject_name}-{subject_id}",
                'object_id': object_id_global,
                'object_name': f"{object_name}-{object_id}",
                'relation_id': relation_id,
                'relation_name': relation_name
            })

        scan_relations[scan_id] = relations

    return scan_relations


def load_3dssg(data_dir):
    scan_objects, id2global, global2label = load_objects(data_dir)
    scan_relations = load_relationships(data_dir, id2global, global2label)
    return scan_objects, scan_relations
