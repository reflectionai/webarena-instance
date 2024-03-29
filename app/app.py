from enum import Enum, auto
import subprocess
import time
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


def update_state():
    if get_state() == 'RESETTING' and is_container_healthy('gitlab'):
        set_state(State.READY)


def is_container_healthy(container_name: str):
    """Function to check the container's health status and update the app's state."""
    result = subprocess.run([
        'docker', 'inspect', '--format={{json .State.Health.Status}}',
        container_name
    ],
                            check=True,
                            stdout=subprocess.PIPE)
    health_status = result.stdout.decode('utf-8').strip().strip('"')

    return health_status == "healthy"


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
    update_state()
    if get_state() == 'READY':
        set_state(State.RUNNING)
        return "Instance in use", 200
    else:
        return "Instance not ready", 400


@app.route('/get_state', methods=['GET'])
def get_state_endpoint():
    update_state()
    return get_state(), 200


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
