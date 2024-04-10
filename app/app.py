import asyncio
from datetime import datetime, timedelta
import logging
from dataclasses import dataclass
from enum import Enum, auto
from asyncio.locks import Lock
import random

import fastapi
from fastapi.middleware import cors


class LifespanManager:

  def __init__(self, app: fastapi.FastAPI):
    self.app = app

  async def __aenter__(self):
    asyncio.create_task(state.heartbeat_monitor(debug=True,
                                                container_name=None))

  async def __aexit__(self, *_):
    pass


DEBUG = True
HEARTBEAT_TIMEOUT = timedelta(minutes=5)

app = fastapi.FastAPI(lifespan=LifespanManager)

app.add_middleware(
    cors.CORSMiddleware,
    allow_origins=[
        "http://localhost:5173", "http://127.0.0.1:5173",
        "http://genesis-frontend.storage.googleapis.com"
    ],
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
  last_heartbeat: datetime = datetime.now()  # Initialize with the current time

  async def acquire(self, debug: bool, container_name: None | str):
    await self.check_heartbeat(debug, container_name)
    async with self.lock:
      # Mark as running when in use
      if await self.is_ready():
        self.set_in_use()
        return {"message": "Acquired instance"}, 200

      else:
        raise fastapi.HTTPException(
            status_code=400,
            detail=f"Instance state: {await self.get_status_name()}")

  async def check_heartbeat(self, debug: bool, container_name: None | str):
    # Check if the current time exceeds the last heartbeat by the threshold
    time_since_heartbeat = datetime.now() - self.last_heartbeat
    print(f"Time since heartbeat: {time_since_heartbeat}")
    if time_since_heartbeat > HEARTBEAT_TIMEOUT:
      perform_reset = False
      async with self.lock:
        if self.is_in_use():
          self.set_reset_pending()
          perform_reset = True
      if perform_reset:
        await state.release_instance(debug, container_name)

  async def heartbeat_monitor(self, debug: bool, container_name: None | str):
    """
      Periodically checks if the last heartbeat received is within the acceptable timeframe.
      If not, takes necessary actions.
      """
    while True:
      await asyncio.sleep(60)  # Check every minute
      await self.check_heartbeat(debug=debug, container_name=container_name)

  async def get_status(self) -> Status:
    if await self.is_ready():
      return Status.READY
    return self.status

  async def get_status_name(self):
    status = await self.get_status()
    return status.name

  async def is_ready(self):
    return self.status == Status.RESETTING  # and await is_container_healthy( 'gitlab')

  async def release_instance(self, debug: bool, container_name: None | str):
    containers = {
        # 'gitlab': ['8023:8023', 'snapshot-gitlab:initial'],
        # 'shopping': ['7770:80', 'snapshot-shopping:initial'],
        'shopping_admin': ['7780:80', 'snapshot-shopping_admin:initial'],
        # 'forum': ['9999:80', 'snapshot-forum:initial'],
    }
    if container_name is not None:
      containers = {container_name: containers[container_name]}

    for container, [port, image] in containers.items():
      try:
        # Stop and remove the container
        if not debug:
          await run("docker", "stop", container)
          await run("docker", "rm", container)
          await run("docker", "run", "-d", "--name", container, "-p", port,
                    image)
      except AsyncioException as e:
        logging.error(f"Error releasing {container}: {e}")
        # Handle errors in the subprocess execution
        async with self.lock:
          self.set_down()
          return
    async with self.lock:
      self.set_resetting()

  def is_in_use(self):
    return self.status == Status.IN_USE

  def set_down(self):
    self.status = Status.DOWN

  def set_in_use(self):
    if self.status != Status.RESETTING:
      raise StateException(f"Invalid state: {self.status}")
    self.status = Status.IN_USE

  def set_reset_pending(self):
    if self.status != Status.IN_USE:
      raise StateException(f"Invalid state: {self.status}")
    self.status = Status.RESET_PENDING

  def set_resetting(self):
    if self.status != Status.RESET_PENDING:
      raise StateException(f"Invalid state: {self.status}")
    self.status = Status.RESETTING

  def update_heartbeat(self):
    self.last_heartbeat = datetime.now()


state = State(Status.RESETTING, Lock())


async def is_container_healthy(container_name: str):
  """Function to check the container's health status and update the app's state."""
  if DEBUG:
    return random.choice([True, False])
  else:
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


async def _release(background_tasks: fastapi.BackgroundTasks, debug: bool,
                   container_name: None | str):
  perform_release = False
  async with state.lock:
    if not state.is_in_use():
      raise fastapi.HTTPException(
          status_code=400,
          detail=
          f"Instance cannot be released. State: {await state.get_status_name()}"
      )

    state.set_reset_pending()
    perform_release = True
  if perform_release:
    background_tasks.add_task(state.release_instance, debug, container_name)
  return {"message": "Reset initiated" + (" (debug)" if debug else "")}, 202


@app.post('/acquire-debug')
async def acquire_debug():
  return await state.acquire(debug=True, container_name=None)


@app.post('/acquire')
async def acquire(container_name: None | str = None):
  return await state.acquire(debug=False, container_name=container_name)


@app.post('/heartbeat')
async def heartbeat():
  state.update_heartbeat()
  return {"message": "Heartbeat received"}, 200


@app.post('/release')
async def release(background_tasks: fastapi.BackgroundTasks,
                  container_name: None | str = None):
  return await _release(background_tasks,
                        debug=False,
                        container_name=container_name)


@app.post('/release-debug')
async def release_debug(background_tasks: fastapi.BackgroundTasks):
  return await _release(background_tasks, debug=True, container_name=None)


@app.get('/status')
async def status():
  async with state.lock:
    return {"status": await state.get_status_name()}
