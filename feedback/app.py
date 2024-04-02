from flask import Flask, render_template


app = Flask(__name__)


@app.route('/')
def index():
    import json
    data_path = "data/3DSSG/feedback/0cac75dc-8d6f-2d13-8d08-9c497bd6acdc.json"
    with open(data_path, 'r') as f:
        data = json.load(f)

    return render_template('index.html', data=data)


if __name__ == '__main__':
    app.run()
