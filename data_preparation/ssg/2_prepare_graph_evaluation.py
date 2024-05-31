import argparse
import json
import os
import logging

from tqdm import tqdm


logger = logging.getLogger('sid')
logger.setLevel(logging.INFO)


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--data_dir', type=str,
                        default="data/3DSSG/raw/",
                        help="Path to the 3DSSG dataset")
    return parser.parse_args()


def main():
    args = parse_args()

    # Check if the objects file exists
    objects_file = os.path.join(args.data_dir, "objects.json")
    if not os.path.exists(objects_file):
        logger.error(f"File not found: {objects_file}")
        return

    # Check if the scenarios file exists
    scenarios_file = os.path.join(args.data_dir, "scenarios.json")
    if not os.path.exists(scenarios_file):
        logger.error(f"File not found: {scenarios_file}")
        return

    # Load the 3DSSG dataset
    with open(objects_file, 'r') as f:
        objects = json.load(f)['scans']
        logger.info(f"Loaded {len(objects)} scans from {objects_file}")

    with open(scenarios_file, 'r') as f:
        scenarios = json.load(f)['scans']
        logger.info(f"Loaded {len(scenarios)} scans from {scenarios_file}")

    # Define save path
    feedback_file = os.path.join(args.data_dir, "feedback.json")
    logger.info(f"Saving feedback data to {feedback_file}")

    # Build an index
    objects_index = {item['scan']: item for item in objects}
    scenarios_index = {item['scan']: item for item in scenarios}

    # Process the data
    feedback = []
    for scan_id in tqdm(scenarios_index, desc="Processing scenarios"):
        # Get scan data
        object_data = objects_index[scan_id]['objects']
        scan_objects = [o['label'] for o in object_data]

        # Get scenario data
        for item in scenarios_index[scan_id]['scenarios']:
            # Get scenario data
            scenario = item['scenario']
            scenario_objects = item['objects']

            # Build the feedback data
            # Select the scan objects that are part of the scenario
            # This will be used to pre-select the objects in the feedback form
            # when asking for human feedback
            feedback.append({
                'scan': scan_id,
                'scenario': scenario,
                'objects': [{
                    'label': o,
                    'selected': o in scenario_objects,
                } for o in scan_objects],
            })

    # Save the feedback data
    with open(feedback_file, 'w') as f:
        json.dump({'scans': feedback}, f, indent=4)


if __name__ == "__main__":
    main()
