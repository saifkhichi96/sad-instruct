import json
import random

scene_graph_file = "data/3DSSG/scenarios_train.json"
instructions_file = "data/3DSSG/instructions copy.json"

with open(scene_graph_file, 'r') as f:
    scene_graph_data = json.load(f)

with open(instructions_file, 'r') as f:
    instructions_data = json.load(f)

data = []
for idx, item in enumerate(instructions_data):
    if item['instructions'].startswith('Error: '):
        continue

    scan_id = item['scan_id']
    scenario = item['scenario']

    sg = scene_graph_data[idx]
    if scan_id == sg['scan_id'] and scenario == sg['scenario_description']:
        data.append({
            'scan_id': scan_id,
            'scenario': scenario,
            'instructions': item['instructions'],
            'scene_graph': {
                'objects': sg['scenario_objects'],
                'relations': sg['scenario_relations']
            }
        })

# Shuffle the data
random.shuffle(data)

# Create splits
num_samples = len(data)
num_train = int(num_samples * 0.8)
train_data = data[:num_train]
test_data = data[num_train:]

print('Training samples:', len(train_data))
print('Testing samples:', len(test_data))

def process_item(item):
    sg = json.dumps(item["scene_graph"])
    return {
        "messages": [
            {"role": "system",
                "content": "You are a situational instructions AI who generates step-by-step instructions for performing tasks or completing scenarios in real-world 3D scenes given a partial (scenario-specific) scene-graph of the scene and the description of the task to perform."},
            {"role": "user",
                "content": f"Given the scene graph: {sg}, I want to do the task: {item['scenario']}"},
            {"role": "assistant", "content": item['instructions']}
        ]
    }

# Create conversations
train_conversations = [process_item(i) for i in train_data]
test_conversations = [process_item(i) for i in test_data]

# Save the dataset
train_path = 'ft_train.jsonl'
with open(train_path, 'w') as f:
    for item in train_conversations:
        f.write(json.dumps(item) + '\n')

test_path = 'ft_test.jsonl'
with open(test_path, 'w') as f:
    for item in test_conversations:
        f.write(json.dumps(item) + '\n')

print(f'Training data saved to {train_path}')
print(f'Testing data saved to {test_path}')
