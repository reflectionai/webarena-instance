from enum import Enum, auto
import subprocess
from flask import Flask
import os

app = Flask(__name__)


class State(Enum):
    UNKNOWN = auto()
    RESETTING = auto()
    READY = auto()
    RUNNING = auto()


def set_state(state: State):
    os.environ['INSTANCE_STATE'] = state.name


def get_state():
    return os.environ.get('INSTANCE_STATE', 'unknown')


@app.route('/reset', methods=['POST'])
def reset():
    # Your reset logic here
    set_state(State.RESETTING)
    containers = {
        'gitlab': ['8023:8023', 'snapshot-gitlab:initial'],
        'shopping': ['7770:80', 'snapshot-shopping:initial'],
        'shopping_admin': ['7780:80', 'snapshot-shopping_admin:initial'],
        'forum': ['9999:80', 'snapshot-forum:initial'],
    }

    for container, [port, image] in containers.items():
        try:
            # Stop and remove the container
            subprocess.run(["docker", "stop", container], check=True)
            subprocess.run(["docker", "rm", container], check=True)
            # Run the container from the snapshot image
            subprocess.run([
                "docker", "run", "-d", "--name", container, "-p", port, image
            ],
                           check=True)
        except subprocess.CalledProcessError as e:
            # Handle errors in the subprocess execution
            return f"An error occurred: {e}", 500

    # Reset logic continues
    return "Reset complete", 200


@app.route('/use', methods=['POST'])
def use():
    # Mark as running when in use
    set_state(State.RUNNING)
    return "Instance in use", 200


@app.route('/get_state', methods=['GET'])
def get_state_endpoint():
    return get_state(), 200


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
