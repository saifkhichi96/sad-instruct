import argparse
import os
import json

from tqdm import tqdm


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--data_dir', type=str,
                        default="data/3DSSG/raw/",
                        help="Path to the 3DSSG dataset")
    return parser.parse_args()


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


def main():
    args = parse_args()

    # Load 3DSSG dataset
    print(f"Loading 3DSSG dataset from {args.data_dir}")
    scan_objects, scan_relations = load_3dssg(args.data_dir)
    print(f"- Loaded object data for {len(scan_objects)} scans")
    print(f"- Loaded relationships data for {len(scan_relations)} scans")
    print()

    # Load the scenarios and feedback data
    print(f"Loading scenarios and feedback data from {args.data_dir}")
    scenarios_file = os.path.join(args.data_dir, "scenarios.json")
    feedback_file = os.path.join(args.data_dir, "feedback_response.json")

    # Load the dataset
    with open(scenarios_file, 'r') as f:
        scenarios = json.load(f)['scans']
    with open(feedback_file, 'r') as f:
        feedback = json.load(f)['scans']

    # Build an index
    scenarios_index = {item['scan']: item for item in scenarios}
    feedback_index = {(item['scan'], item['scenario']): item for item in feedback}
    print(f"- Loaded scenarios data for {len(scenarios_index)} scans")
    print(f"- Loaded feedback data for {len(feedback_index)} scenarios")
    print()

    # Process the data
    updated_scenarios = []
    num_updated = 0
    total_scenarios = 0
    for scan_id in tqdm(scenarios_index, desc="Refining scenarios"):
        # Get scan data
        scan_data = scenarios_index[scan_id]
        scan_scenarios = scan_data['scenarios']

        # Update the scenarios
        for scenario in scan_scenarios:
            scenario_desc = scenario['scenario']

            # Find the feedback for the scenario
            feedback_item = feedback_index.get((scan_id, scenario_desc), None)
            if feedback_item is not None:
                feedback_objs = [o['label'] for o in feedback_item['objects'] if o['selected']]
                scenario['objects'] = feedback_objs
                num_updated += 1
            total_scenarios += 1
        updated_scenarios.append(scan_data)

    # Index scenario data
    scenario_data = {item['scan']: item for item in updated_scenarios}
    print(f"- Processed {total_scenarios} scenarios in {len(scenario_data)} scans")
    print(f"- Updated {num_updated} scenarios with feedback")
    print(f"- [WARNING] {total_scenarios - num_updated} scenarios did not have feedback")
    print()

    # Create scenario-specific scene graphs
    data = []
    num_skipped = 0
    num_processed = 0
    for scan_id, scan_objects_ in tqdm(scan_objects.items(), desc="Pruning scene graphs"):
        # Get scan relations
        scan_relations_ = scan_relations.get(scan_id, [])

        # Get scan scenarios
        scan_scenarios = scenario_data[scan_id]['scenarios']

        # Process each scenario
        for scenario in scan_scenarios:
            num_processed += 1
            scenario_description = scenario['scenario']
            scenario_object_names = scenario['objects']

            # Get details of scenario objects
            scenario_objects = [o for o in scan_objects_ if o['label'] in scenario_object_names]
            scenario_objects_ids = [str(o['global_id']) for o in scenario_objects]

            # Get details of scenario relations
            scenario_relations = []
            for rel in scan_relations_:
                if rel['subject_id'] in scenario_objects_ids and rel['object_id'] in scenario_objects_ids:
                    scenario_relations.append(rel)

            # Skip if no relations found
            if len(scenario_relations) == 0:
                num_skipped += 1
                # continue

            # Create the data sample
            data.append({
                'scan': scan_id,
                # Uncomment to save the full scene graph data for the scan
                # (this will increase the file size significantly, we recommend
                # keeping this commented, you can always read the full scene graph
                # data from the original 3DSSG dataset files if needed)
                # 'objects': scan_objects_,
                # 'relations': scan_relations_,
                'scenario': scenario_description,
                # Scenario-specific scene graph data
                'scenario_objects': scenario_objects,
                'scenario_relations': scenario_relations
            })
    print(f"- Processed {num_processed} scenarios")
    print(f"- [WARNING] {num_skipped} scenarios have no relations")
    print()

    # Pretty print one data sample
    print("Sample data:")
    sample = data[0].copy()
    # sample['objects'] = '...'
    # sample['relations'] = '...'
    if len(sample['scenario_objects']) > 2:
        sample['scenario_objects'] = sample['scenario_objects'][:2]
    if len(sample['scenario_relations']) > 2:
        sample['scenario_relations'] = sample['scenario_relations'][:2]
    print(json.dumps(sample, indent=4))
    print()

    # Save the refined data
    updated_file = os.path.join(args.data_dir, "scenarios_refined.json")
    print(f"Saving refined data with {len(data)} samples to {updated_file}")
    with open(updated_file, 'w') as f:
        json.dump({'scans': data}, f)


if __name__ == '__main__':
    main()
