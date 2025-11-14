import os, requests, json
ENDPOINT = os.environ.get("ENDPOINT", "http://localhost:8080/llm-analysis-quiz")
TEST_EMAIL = os.environ.get("TEST_EMAIL", "25ds1000013@ds.study.iitm.ac.in")
TEST_SECRET = os.environ.get("TEST_SECRET", "secret_llm_p2")
DEMO_URL = "https://tds-llm-analysis.s-anand.net/demo"
payload = {"email": TEST_EMAIL, "secret": TEST_SECRET, "url": DEMO_URL}
r = requests.post(ENDPOINT, json=payload, timeout=200)
print("status:", r.status_code)
try:
    print(r.json())
except Exception:
    print(r.text[:1000])
