import json
import os
import threading
from flask import Flask, render_template

from prompting import SceneGraph

app = Flask(__name__)


lock = threading.Lock()


def visualize(messages, path):
    with lock:
        path = f'feedback{path}'
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
    instructions_path = "data/3DSSG/instructions_correct.json"
    with open(instructions_path, 'r') as f:
        instructions = json.load(f)

    # Parse messages and try to convert content to JSON where possible
    parsed_instructions = []
    for i, instruction in enumerate(instructions):
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

        parsed_instructions.append({**instruction, 'sg': sg_path})

    return render_template('instructions.html',
                           instructions=parsed_instructions,
                           data_size=len(parsed_instructions),
                           status=read_file('screenlog.0'))

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--host', type=str, default='0.0.0.0')
    parser.add_argument('--port', type=int, default=15000)
    args = parser.parse_args()

    app.run(
        host=args.host,
        port=args.port,
        debug=True
    )
