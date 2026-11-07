"""Supervisor: runs Uvicorn (API) and the Telegram bot as two independent processes.
If one crashes it is restarted alone; the other keeps running."""
import os, secrets, subprocess, sys, time, signal
env = dict(os.environ)
if not env.get("API_ADMIN_TOKEN"):  # shared secret between API and bot; not needed for the bot to start
    env["API_ADMIN_TOKEN"] = secrets.token_urlsafe(32)
port = env.get("PORT") or env.get("API_PORT") or "8080"
env.setdefault("API_BASE_URL", f"http://127.0.0.1:{port}")
CMDS = {
    "api": [sys.executable, "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", port],
    "bot": [sys.executable, "-u", "bot.py"],
}
procs, delay, started = {}, {k: 2 for k in CMDS}, {}
stop = False
def shutdown(*_):
    global stop; stop = True
    for p in procs.values():
        if p.poll() is None: p.terminate()
signal.signal(signal.SIGTERM, shutdown); signal.signal(signal.SIGINT, shutdown)
while not stop:
    for name, cmd in CMDS.items():
        p = procs.get(name)
        if p is None or p.poll() is not None:
            if p is not None:
                print(f"[run] {name} exited with {p.returncode}; restarting in {delay[name]}s", flush=True)
                if time.time() - started[name] > 60: delay[name] = 2
                if time.time() < started[name] + delay[name]: continue
                delay[name] = min(delay[name] * 2, 60)
            procs[name] = subprocess.Popen(cmd, env=env); started[name] = time.time()
            print(f"[run] started {name}", flush=True)
    time.sleep(1)
for p in procs.values():
    try: p.wait(10)
    except Exception: p.kill()
