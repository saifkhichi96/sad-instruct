import argparse
import os
import json

from tqdm import tqdm

# Local imports
from utils import load_3dssg


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--data_dir', type=str,
                        default="data/3DSSG/raw/",
                        help="Path to the 3DSSG dataset")
    return parser.parse_args()


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
