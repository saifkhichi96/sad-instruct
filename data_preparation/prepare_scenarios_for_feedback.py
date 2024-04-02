import json
import os


# Define paths.
data_dir = "data/3DSSG/scenarios/"
feedback_dir = "data/3DSSG/feedback/"
os.makedirs(feedback_dir, exist_ok=True)

for file in os.listdir(data_dir):
    if not file.endswith(".json"):
        continue

    # Load the data
    data_path = os.path.join(data_dir, file)
    with open(data_path, 'r') as f:
        data = json.load(f)

    scan_id = data['scan']
    object_ids = [obj['label'] for obj in data['objects']]

    # Prepare the human feedback
    feedback = []
    for scenario in data['scenarios']:
        scenario_objects = scenario['objects']
        feedback.append({
            'scans': [scan_id],
            'scenario': scenario['scenario'],
            'objects': [{
                'label': oid,
                'selected': oid in scenario_objects,
            } for oid in object_ids],
        })

    # Save the human feedback
    save_file = os.path.join(feedback_dir, f"{scan_id}.json")

    with open(save_file, 'w') as f:
        json.dump(feedback, f, indent=4)
