import json
import random
import threading

from flask import Flask, render_template, redirect, request, url_for


# Create a new Flask app
app = Flask(__name__)

# Create a lock for thread safety
lock = threading.Lock()


@app.route('/')
def index():
    with lock:
        # Load the feedback data
        feedback_file = "data/3DSSG/raw/feedback.json"
        with open(feedback_file, 'r') as f:
            feedback_data = json.load(f)['scans']

        # Load the feedback response data
        response_file = "data/3DSSG/raw/feedback_response.json"
        with open(response_file, 'r') as f:
            response_data = json.load(f)['scans']

    # Build an index
    feedback_index = {}
    for feedback in feedback_data:
        scan_id = feedback['scan']
        scenario = feedback['scenario']
        feedback_index[f'{scan_id}-{scenario}'] = feedback

    # Filter completed files
    completed = []
    for response in response_data:
        scan_id = response['scan']
        scenario = response['scenario']
        completed.append(f'{scan_id}-{scenario}')

    # Filter queue files
    queue = [i for i in feedback_index if i not in completed]

    # Select a random item from the queue
    selected_item = random.choice(queue)
    selected_data = feedback_index[selected_item]

    return render_template('feedback.html',
                           key=selected_item,
                           data=selected_data,
                           num_total=len(feedback_index),
                           num_done=len(completed))


@app.route('/submit', methods=['POST'])
def submit():
    with lock:
        # Load the feedback data
        feedback_file = "data/3DSSG/raw/feedback.json"
        with open(feedback_file, 'r') as f:
            feedback_data = json.load(f)['scans']

        # Load the feedback response data
        response_file = "data/3DSSG/raw/feedback_response.json"
        with open(response_file, 'r') as f:
            response_data = json.load(f)['scans']

    # Build an index
    feedback_index = {}
    for feedback in feedback_data:
        scan_id = feedback['scan']
        scenario = feedback['scenario']
        feedback_index[f'{scan_id}-{scenario}'] = feedback

    # Read form data
    form_data = request.form
    key = form_data['key']

    # Find original data
    item = feedback_index[key]
    scan_id = item['scan']
    scenario = item['scenario']
    objects = item['objects']

    for oid, o in enumerate(objects):
        checkbox_name = f'obj-{oid}'
        if checkbox_name in form_data:
            o["selected"] = True
        else:
            o["selected"] = False
 
    # Add the updated data to the response data
    response_data.append({
        'scan': scan_id,
        'scenario': scenario,
        'objects': objects,
    })

    # Save the updated data
    with lock:
        with open(response_file, 'w') as f:
            json.dump({'scans': response_data}, f, indent=4)

    # Redirect to the index page
    return redirect(url_for('index'))


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--host', type=str, default='0.0.0.0')
    parser.add_argument('--port', type=int, default=5000)
    args = parser.parse_args()

    app.run(
        host=args.host,
        port=args.port,
        debug=False
    )
