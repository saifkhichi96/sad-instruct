import json
import os
import random
import threading

from flask import Flask, render_template

# Local imports
from utils import SceneGraph


# Create a new Flask app
app = Flask(__name__)

# Create a lock for thread safety
lock = threading.Lock()


def visualize(messages, path):
    with lock:
        path = f'src{path}'
        if messages and not os.path.exists(path):
            scene_graph = SceneGraph.parse(messages[0]['content'].split('{')[1].split('}')[0])
            scene_graph.visualize(path)


def read_file(logfile):
    if not os.path.exists(logfile):
        return ''

    with open(logfile, 'r') as f:
        lines = f.readlines()
        return lines[-1] if lines else ''


@app.route('/')
def index():
    instructions_path = "data/3DSSG/instructions_lq.json"
    with open(instructions_path, 'r') as f:
        instructions = json.load(f)
    
    objects_path = "data/3DSSG/raw/objects.json"
    with open(objects_path, 'r') as f:
        objects = json.load(f)['scans']
    objects = {o['scan']: o['objects'] for o in objects}

    scenarios_path = "data/3DSSG/raw/scenarios_refined.json"
    with open(scenarios_path, 'r') as f:
        scenarios = json.load(f)['scans']
    scenarios = {(s['scan'], s['scenario']): s['scenario_objects'] for s in scenarios}

    # Select 100 random instructions
    random.seed(42)
    num_total = len(instructions)
    instructions = random.sample(instructions, 100)

    # Parse messages and try to convert content to JSON where possible
    parsed_instructions = []
    for i, instruction in enumerate(instructions):
        scan_id = instruction['scan_id']
        scenario = instruction['scenario']
        scan_objects = set([o['label'] for o in objects[scan_id]])
        scenario_objects = set([o['label'] for o in scenarios[(scan_id, scenario)]])
        items =  [{
                'label': o,
                'selected': o in scenario_objects,
        } for o in scan_objects]
        conversation = instruction['conversation']
        try:
            instruction['instructions'] = list(json.loads(instruction['instructions']).values())
        except Exception:
            continue
        for msg in conversation:
            try:
                msg['content'] = json.loads(msg['content'])

                # If successful, convert this into an HTML list
                if isinstance(msg['content'], dict):
                    msg['content'] = '<ol>' + ''.join([f'<li>{item}</li>' for item in msg['content'].values()]) + '</ol>'
            except Exception:
                pass
        
        # Extract the scene graph from first user message
        user_messages = [msg for msg in conversation if msg['role'] == 'user']
        sg_path = f'/static/scene_graph_{i}.png'
        threading.Thread(target=visualize, args=(user_messages, sg_path)).start()

        parsed_instructions.append({**instruction, 'sg': sg_path, 'items': items})


    return render_template('viewer.html',
                           instructions=parsed_instructions,
                           data_size=num_total)

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--host', type=str, default='0.0.0.0')
    parser.add_argument('--port', type=int, default=5001)
    args = parser.parse_args()

    app.run(
        host=args.host,
        port=args.port,
        debug=True
    )
