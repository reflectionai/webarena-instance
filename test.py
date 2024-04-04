import asyncio
import httpx
import random
from collections import Counter
from app import app  # Import your FastAPI app here
import pytest

ACTIONS_PER_BACKEND = 50  # Number of actions per frontend
NUM_FRONTENDS = 20  # Example: number of concurrent frontends to simulate
NUM_BACKENDS = 20  # Example: number of backend instances
BACKENDS = [
    f"http://localhost:{port}" for port in range(8000, 8000 + NUM_BACKENDS)
]  # Example backend URLs

random.seed(42)


async def random_sleep():
  await asyncio.sleep(random.random() * 0.1)


assignments: list[tuple[int, str]] = []


@pytest.mark.asyncio
async def test_fuzz():

  async def simulate_frontend(url: str):
    async with httpx.AsyncClient(app=app.app, base_url=url) as client:
      # iterate through the repeated frontends list in random order
      for _ in range(ACTIONS_PER_BACKEND):
        frontend_id = random.randint(0, NUM_FRONTENDS - 1)
        action_name = random.choice(
            ("acquire", "heartbeat", "status", "release"))
        match action_name:
          case "acquire":
            response = await client.post("/acquire-debug")
            if response.status_code == 200:
              assignments.append((frontend_id, url))
          case "heartbeat":
            await client.post("/heartbeat")
          case "status":
            await client.get("/status")
          case "release":
            await client.post("/release-debug")
            for frontend, backend in assignments:
              if frontend == frontend_id and backend == url:
                assignments.remove((frontend, backend))
        await random_sleep()

      frontends = list(range(NUM_FRONTENDS))
      random.shuffle(frontends)
      for frontend_id in frontends:
        # perform an acquire action (in case none was chosen randomly)
        response = await client.post("/acquire-debug")
        if response.status_code == 200:
          assignments.append((frontend_id, url))
        await random_sleep()

      random.shuffle(frontends)
      for frontend_id in frontends:
        # perform a final reset action in order to return all backends to the ready state
        await client.post("/release-debug")
        await random_sleep()

  # execute actions asynchronously against each backend
  await asyncio.gather(*(simulate_frontend(url) for url in BACKENDS))


@pytest.mark.asyncio
async def test_unique_assignments():
  # check that there is at most one frontend per backend
  backends_per_frontend = Counter[int]()
  frontends_per_backend = Counter[str]()
  for frontend_id, url in assignments:
    backends_per_frontend[frontend_id] += 1
    frontends_per_backend[url] += 1
  for frontend_id, count in backends_per_frontend.items():
    assert count == 1, f"Frontend {frontend_id} was assigned to multiple backends"
  for backend_id, count in frontends_per_backend.items():
    assert 0 <= count <= 1, f"Backend {backend_id} was assigned to multiple frontends"


@pytest.mark.asyncio
async def test_ready_resetting():
  # check that all backends have returned to the ready or resetting state
  for url in BACKENDS:
    async with httpx.AsyncClient(app=app.app, base_url=url) as client:
      status_response = await client.get("/status")
      status = status_response.json()["status"]
      assert status in [
          app.Status.READY.name,
          app.Status.RESETTING.name,
      ], f"Backend {url} status was {status}"
