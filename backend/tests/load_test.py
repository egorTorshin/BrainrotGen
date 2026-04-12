import random
import uuid
from locust import HttpUser, task, between, events

class BrainrotUser(HttpUser):
    wait_time = between(1, 3)
    token = None
    username = None

    def on_start(self):
        """Register/Login at the start of the session"""
        self.username = f"user_{uuid.uuid4().hex[:8]}"
        password = "testpassword123"

        # 1. Register
        resp = self.client.post(
            "/api/v1/auth/register",
            json={"username": self.username, "password": password}
        )
        if resp.status_code == 201:
            self.token = resp.json().get("access_token")
        else:
            # Try login if already exists (shouldn't happen with UUID)
            resp = self.client.post(
                "/api/v1/auth/login",
                json={"username": self.username, "password": password}
            )
            if resp.status_code == 200:
                self.token = resp.json().get("access_token")

    @property
    def headers(self):
        return {"Authorization": f"Bearer {self.token}"} if self.token else {}

    @task(3)
    def check_quota(self):
        """Verify daily quota status"""
        if not self.token:
            return
        self.client.get("/api/v1/jobs/quota", headers=self.headers, name="/jobs/quota")

    @task(1)
    def create_and_poll_job(self):
        """Simulate a full flow: create job -> poll status"""
        if not self.token:
            return

        # Create job
        payload = {
            "text": "This is a performance test script for BrainrotGen.",
            "voice": random.choice(["male", "female"]),
            "background": random.choice(["minecraft", "subway"])
        }
        resp = self.client.post("/api/v1/jobs", json=payload, headers=self.headers, name="/jobs (POST)")

        if resp.status_code == 201:
            job_id = resp.json().get("job_id")
            # Poll status a few times
            for _ in range(2):
                self.client.get(f"/api/v1/jobs/{job_id}", headers=self.headers, name="/jobs/{id}")

    @task(5)
    def health_check(self):
        """Lightweight health check"""
        self.client.get("/api/v1/health", name="/health")

@events.init_command_line_parser.add_listener
def _(parser):
    parser.add_argument("--p95-threshold", type=float, default=200.0, help="P95 latency threshold in ms")

@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Check if P95 requirement is met after the test"""
    print("\n" + "="*40)
    print("PERFORMANCE GATE CHECK")
    print("="*40)

    p95_threshold = environment.parsed_options.p95_threshold
    all_passed = True

    for name, stats in environment.stats.entries.items():
        if name == "Total":
            continue

        p95 = stats.get_response_time_percentile(0.95)
        print(f"Endpoint: {name}")
        print(f"  P95 Latency: {p95:.2f}ms (Goal: <{p95_threshold}ms)")

        if p95 > p95_threshold:
            print(f"  [FAIL] P95 exceeds threshold!")
            all_passed = False
        else:
            print(f"  [PASS]")

    if not all_passed:
        print("\nRESULT: FAILED - Performance gates not met.")
        # environment.process_exit_code = 1 # Optional: fail the process
    else:
        print("\nRESULT: PASSED - All endpoints within performance limits.")
