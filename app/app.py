import asyncio
import logging
from dataclasses import dataclass
from enum import Enum, auto
from asyncio.locks import Lock

from fastapi import FastAPI, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class Status(Enum):
    RESET_PENDING = auto()
    RESETTING = auto()
    READY = auto()
    IN_USE = auto()
    DOWN = auto()


class StateException(Exception):
    pass


@dataclass
class State:
    status: Status
    lock: Lock

    async def reset_started(self):
        return self.status == Status.RESETTING

    async def is_ready(self):
        return self.status == Status.RESETTING and await is_container_healthy(
            'gitlab')

    def is_in_use(self):
        return self.status == Status.IN_USE

    def set_reset_pending(self):
        if self.status != Status.IN_USE:
            raise StateException(f"Invalid state: {self.status}")
        self.status = Status.RESET_PENDING

    def set_resetting(self):
        if self.status != Status.RESET_PENDING:
            raise StateException(f"Invalid state: {self.status}")
        self.status = Status.RESETTING

    def set_in_use(self):
        if self.status != Status.RESETTING:
            raise StateException(f"Invalid state: {self.status}")
        self.status = Status.IN_USE

    def set_down(self):
        self.status = Status.DOWN

    def raise_state_error(self):
        raise StateException(f"Invalid state: {self.status}")

    async def get_status_name(self):
        if await state.is_ready():
            return Status.READY.name
        return state.status.name


state = State(Status.RESETTING, Lock())


async def is_container_healthy(container_name: str):
    """Function to check the container's health status and update the app's state."""
    health_status = await run('docker', 'inspect',
                              '--format={{json .State.Health.Status}}',
                              container_name)
    return health_status == "healthy"


class AsyncioException(Exception):
    pass


async def run(*args: str) -> str:
    proc = await asyncio.create_subprocess_exec(*args,
                                                stdout=asyncio.subprocess.PIPE,
                                                stderr=asyncio.subprocess.PIPE)
    stdout, stderr = await proc.communicate()
    if proc.returncode != 0:
        raise AsyncioException(
            f"Command failed with exit code {proc.returncode}: {stderr.decode().strip()}"
        )
    return stdout.decode('utf-8').strip().strip('"')


async def release_instance(debug: bool):
    containers = {
        'gitlab': ['8023:8023', 'snapshot-gitlab:initial'],
        'shopping': ['7770:80', 'snapshot-shopping:initial'],
        'shopping_admin': ['7780:80', 'snapshot-shopping_admin:initial'],
        'forum': ['9999:80', 'snapshot-forum:initial'],
    }

    for container, [port, image] in containers.items():
        try:
            # Stop and remove the container
            if debug:
                await asyncio.sleep(.01)
            else:
                await run("docker", "stop", container)
                await run("docker", "rm", container)
                await run("docker", "run", "-d", "--name", container, "-p",
                          port, image)
        except AsyncioException as e:
            logging.error(f"Error releasing {container}: {e}")
            # Handle errors in the subprocess execution
            async with state.lock:
                state.set_down()
                return
    async with state.lock:
        state.set_resetting()


async def _release(background_tasks: BackgroundTasks, debug: bool):
    async with state.lock:
        if not state.is_in_use():
            return {
                "error":
                f"Instance cannot be released. State: {await state.get_status_name()}"
            }, 400

        state.set_reset_pending()
    background_tasks.add_task(release_instance, debug)
    return {
        "message": "Release initiated" + (" (debug)" if debug else "")
    }, 202


@app.post('/release')
async def release(background_tasks: BackgroundTasks):
    return await _release(background_tasks, debug=False)


@app.post('/release-debug')
async def release_debug(background_tasks: BackgroundTasks):
    return await _release(background_tasks, debug=True)


@app.put('/acquire')
async def acquire():
    async with state.lock:
        # Mark as running when in use
        if await state.is_ready():
            state.set_in_use()
            return {"message": "Acquired instance"}, 200

        else:
            return {
                "error": f"Instance state: {await state.get_status_name()}"
            }, 400


@app.get('/status')
async def status():
    async with state.lock:
        return {"status": await state.get_status_name()}
