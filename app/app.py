from enum import Enum, auto
import subprocess
from threading import Lock

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

state_file_path = "/tmp/app_state.json"  # Path to the state file
state_lock = Lock()  # Lock to ensure atomic updates to the state file


class State(Enum):
    RESETTING = auto()
    READY = auto()
    RUNNING = auto()


def set_state(state: State):
    with state_lock:
        with open(state_file_path, "w") as f:
            f.write(state.name)


def get_state() -> State:
    with state_lock:
        try:
            with open(state_file_path, "r") as f:
                state_data = f.read()
                return State(state_data)
        except FileNotFoundError:
            # If the state file doesn't exist, assume RESETTING state
            return State.RESETTING


def update_state():
    if get_state() == State.RESETTING and is_container_healthy('gitlab'):
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


@app.post('/reset')
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


@app.post('/use')
def use():
    # Mark as running when in use
    update_state()
    if get_state() == State.READY:
        set_state(State.RUNNING)
        return "Instance in use", 200
    else:
        return "Instance not ready", 400


@app.get('/get_state')
def get_state_endpoint():
    update_state()
    return get_state().name, 200
