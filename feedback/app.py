import json
import os
import random
from flask import Flask, render_template, redirect, request, url_for


app = Flask(__name__)


@app.route('/')
def index():
    queue_path = "data/3DSSG/feedback/"
    completed_path = "data/3DSSG/feedback_response/"

    queue_files = os.listdir(queue_path)
    completed_files = os.listdir(completed_path)

    # Filter queue files to only include those that have not been completed
    queue_files = [f for f in queue_files if f not in completed_files]

    # Select a random file from the queue
    selected_file = random.choice(queue_files)
    data_path = os.path.join(queue_path, selected_file)
    with open(data_path, 'r') as f:
        data = json.load(f)

    return render_template('index.html',
                           data=data,
                           file_name=selected_file,
                           num_files_total=len(queue_files) + len(completed_files),
                           num_files_done=len(completed_files))


@app.route('/submit', methods=['POST'])
def submit():
    file_name = request.form['file_name']

    data_path = "data/3DSSG/feedback/" + file_name
    with open(data_path, 'r') as f:
        original_data = json.load(f)

    form_data = request.form
    updated_data = original_data.copy()

    for scenario_index, scenario in enumerate(updated_data):
        num_selected = 0
        num_skipped = 0
        for object_index, obj in enumerate(scenario['objects']):
            checkbox_name = f'object-{scenario_index}-{object_index}'
            if checkbox_name in form_data:
                obj["selected"] = True
                num_selected += 1
            else:
                obj["selected"] = False
                num_skipped += 1

    # Save the updated data to a new file
    save_path = "data/3DSSG/feedback_response/" + file_name
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    with open(save_path, 'w') as f:
        json.dump(updated_data, f, indent=4)

    # Redirect to the index page
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run()
