"""
brute_force_attack.py

Educational simulation of brute-force password attacks.

Classes
-------
BruteForceAttack        — baseline, single-threaded brute-force
                          (≤4 chars, lowercase only by default)
FastBruteForceAttack    — parallelised brute-force with live-resizable
                          worker pool, full charset (a-z A-Z 0-9 symbols),
                          and speed_multiplier (1–10). Max length up to 8.

Architecture (FastBruteForceAttack)
─────────────────────────────────────
Work channel   : queue.Queue(maxsize=512) — a dedicated producer thread
                 generates combinations on-the-fly and feeds the queue.
                 The queue is NEVER written to by resize or stop logic.

Control channel: dict mapping each live Thread → its own threading.Event.
                 set_speed() signals specific workers to stop by setting
                 their individual event; workers exit after their current
                 bcrypt check without touching the queue.

Pause gate     : a single threading.Event shared by all workers.
                 pause() clears it (workers block at .wait());
                 resume() sets it (all workers unblock simultaneously).

⚠  Complexity warning — bcrypt (rounds=12) costs ~250 ms per check.
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Even with 48 threads the effective rate is only ~190 checks/sec.

    Length 4, lowercase only  (26^4  =     456 976) ≈   40 min  at 1x
                                                     ≈    1 min  at 10x
    Length 4, full charset    (95^4  =  81 450 625) ≈  5 days   at 1x
                                                     ≈  2.5 hrs  at 10x
    Length 6, full charset    (95^6  = 735 billion) ≈ decades

These classes exist to demonstrate *why* bcrypt + long passwords are
secure — not to crack real systems.
"""

import itertools
import string
import time
import threading
import queue as _queue
from typing import Callable, Optional, Tuple


# ---------------------------------------------------------------------------
# Shared constants and helpers
# ---------------------------------------------------------------------------

# Full printable ASCII charset: lowercase + uppercase + digits + punctuation
FULL_CHARSET: str = (
    string.ascii_lowercase    # a-z
    + string.ascii_uppercase  # A-Z
    + string.digits           # 0-9
    + string.punctuation      # !"#$%&'()*+,-./:;<=>?@[\]^_`{|}~
)

# Speed multiplier → worker thread count
# Index 0 unused; indices 1–10 map directly.
_SPEED_TO_THREADS = [
    None,  # 0 — unused
    1,     # 1x  — single-threaded baseline
    2,     # 2x
    4,     # 3x
    6,     # 4x
    8,     # 5x
    12,    # 6x
    16,    # 7x
    24,    # 8x
    32,    # 9x
    48,    # 10x — maximum parallelism
]


def _speed_to_workers(speed_multiplier: int) -> int:
    """Map a 1–10 speed multiplier to a thread-pool worker count."""
    if not 1 <= speed_multiplier <= 10:
        raise ValueError("speed_multiplier must be between 1 and 10 inclusive")
    return _SPEED_TO_THREADS[speed_multiplier]


# ---------------------------------------------------------------------------
# BruteForceAttack — baseline, single-threaded
# ---------------------------------------------------------------------------

class BruteForceAttack:
    """
    Educational simulation of a brute-force attack.

    INTENTIONALLY LIMITED to 4 characters and lowercase letters to illustrate
    why longer/complex passwords are exponentially harder to crack.
    Use FastBruteForceAttack for full charset and longer lengths.
    """

    def __init__(
        self,
        max_length: int = 4,
        charset: str = string.ascii_lowercase,
    ) -> None:
        if max_length > 4:
            raise ValueError(
                "BruteForceAttack is capped at 4 characters for educational purposes. "
                "Use FastBruteForceAttack for longer / more complex searches."
            )
        self.max_length = max_length
        self.charset = charset

    def attack(
        self,
        username: str,
        login_system,
        callback: Optional[Callable] = None,
        stop_event: Optional[threading.Event] = None,
    ) -> Tuple[bool, int, float, Optional[str]]:
        """
        Run a single-threaded brute-force attack.

        Callback signature:
            callback(attempts, elapsed_time, current_attempt, success, cracked_password_or_None)
        """
        start = time.time()
        attempts = 0

        for length in range(1, self.max_length + 1):
            for combo in itertools.product(self.charset, repeat=length):
                if stop_event and stop_event.is_set():
                    return False, attempts, time.time() - start, None

                password = "".join(combo)
                attempts += 1

                success, _ = login_system.login_user(username, password)
                elapsed = time.time() - start

                if callback:
                    callback(attempts, elapsed, password, success, password if success else None)

                if success:
                    return True, attempts, elapsed, password

        return False, attempts, time.time() - start, None

    def estimate_attempts(self) -> int:
        """Total candidates this attack will try."""
        n = len(self.charset)
        return sum(n ** l for l in range(1, self.max_length + 1))


# ---------------------------------------------------------------------------
# FastBruteForceAttack — parallelised, producer-queue, live-resizable pool
# ---------------------------------------------------------------------------

class FastBruteForceAttack:
    """
    Parallelised brute-force attack with full charset, configurable length,
    and a live-resizable worker pool.

    Key differences from BruteForceAttack
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    * charset defaults to all printable ASCII (~95 chars)
    * max_length configurable up to 8
    * speed_multiplier (1–10) can be changed mid-attack via set_speed()
    * Uses per-worker stop events — the work queue is never sentinel-polluted
    * Bounded producer queue (maxsize=512) caps RAM regardless of search space

    Callback signature:
        callback(attempts, elapsed_time, current_attempt, success, cracked_password_or_None)
    """

    MAX_SAFE_LENGTH = 8

    def __init__(
        self,
        max_length: int = 4,
        charset: str = FULL_CHARSET,
        speed_multiplier: int = 1,
    ) -> None:
        if max_length > self.MAX_SAFE_LENGTH:
            raise ValueError(
                f"max_length is capped at {self.MAX_SAFE_LENGTH} to prevent "
                "runaway combinatorial explosion in an educational context."
            )
        self.max_length = max_length
        self.charset = charset
        self._speed = speed_multiplier

        self._pool_lock = threading.Lock()
        self._worker_events: dict = {}
        self._internal_stop = threading.Event()
        # Pause gate — set means running, cleared means paused
        self._pause_event = threading.Event()
        self._pause_event.set()  # unpaused by default

    # ------------------------------------------------------------------
    def estimate_attempts(self) -> int:
        """Total candidates this attack will try (exact)."""
        n = len(self.charset)
        return sum(n ** l for l in range(1, self.max_length + 1))

    # ------------------------------------------------------------------
    def pause(self) -> None:
        """Block all workers after their current bcrypt check completes."""
        self._pause_event.clear()

    def resume(self) -> None:
        """Unblock all paused workers."""
        self._pause_event.set()

    # ------------------------------------------------------------------
    def set_speed(self, speed_multiplier: int) -> None:
        """Resize the worker pool live. Never touches the work queue."""
        if not 1 <= speed_multiplier <= 10:
            return
        self._speed = speed_multiplier

        with self._pool_lock:
            if not self._worker_events:
                return

            target = _speed_to_workers(speed_multiplier)
            current = len(self._worker_events)

            if target > current:
                for _ in range(target - current):
                    stop_evt = threading.Event()
                    t = threading.Thread(
                        target=self._worker_fn, args=(stop_evt,), daemon=True
                    )
                    self._worker_events[t] = stop_evt
                    t.start()

            elif target < current:
                excess = current - target
                victims = list(self._worker_events.keys())[:excess]
                for t in victims:
                    self._worker_events[t].set()
                    del self._worker_events[t]

    # ------------------------------------------------------------------
    def attack(
        self,
        username: str,
        login_system,
        callback: Optional[Callable] = None,
        stop_event: Optional[threading.Event] = None,
    ) -> Tuple[bool, int, float, Optional[str]]:

        # ── shared state ──────────────────────────────────────────────
        # Bounded queue caps memory — producer blocks when full
        self._q: _queue.Queue = _queue.Queue(maxsize=512)
        self._internal_stop = threading.Event()
        self._pause_event.set()  # always start unpaused
        self._result: dict = {}
        self._lock = threading.Lock()
        self._attempts = [0]
        self._start = time.time()
        self._username = username
        self._login_system = login_system
        self._callback = callback

        if stop_event:
            def _watch():
                stop_event.wait()
                self._internal_stop.set()
            threading.Thread(target=_watch, daemon=True).start()

        # ── producer thread — generates combinations on-the-fly ───────
        producer_done = threading.Event()

        def producer():
            for length in range(1, self.max_length + 1):
                for combo in itertools.product(self.charset, repeat=length):
                    if self._internal_stop.is_set():
                        producer_done.set()
                        return
                    password = "".join(combo)
                    while not self._internal_stop.is_set():
                        try:
                            self._q.put(password, timeout=0.1)
                            break
                        except _queue.Full:
                            continue
            producer_done.set()

        threading.Thread(target=producer, daemon=True).start()

        # ── spin up initial worker pool ───────────────────────────────
        num_workers = _speed_to_workers(self._speed)
        with self._pool_lock:
            self._worker_events = {}
            for _ in range(num_workers):
                stop_evt = threading.Event()
                t = threading.Thread(
                    target=self._worker_fn, args=(stop_evt,), daemon=True
                )
                self._worker_events[t] = stop_evt
                t.start()

        # ── wait for completion ───────────────────────────────────────
        while True:
            with self._pool_lock:
                alive = {t: e for t, e in self._worker_events.items() if t.is_alive()}
                self._worker_events = alive
                # Done when: no workers alive AND producer has finished
                if not alive and (producer_done.is_set() or self._internal_stop.is_set()):
                    break
            time.sleep(0.05)

        elapsed = time.time() - self._start
        if self._result:
            return True, self._attempts[0], elapsed, self._result["password"]
        return False, self._attempts[0], elapsed, None

    # ------------------------------------------------------------------
    def _worker_fn(self, my_stop: threading.Event) -> None:
        """
        Consumer worker. Exits when:
          - my_stop is set (scale-down via set_speed)
          - _internal_stop is set (password found or external stop)
          - queue is empty AND producer is done
        """
        while not self._internal_stop.is_set() and not my_stop.is_set():
            # Block here while paused; wake immediately when resumed
            self._pause_event.wait()
            if self._internal_stop.is_set() or my_stop.is_set():
                break

            try:
                password = self._q.get(timeout=0.1)
            except _queue.Empty:
                # Queue temporarily empty — could be producer lag or truly done
                # Loop back and check stop conditions before exiting
                continue

            success, _ = self._login_system.login_user(self._username, password)

            with self._lock:
                self._attempts[0] += 1
                snap = self._attempts[0]

            elapsed = time.time() - self._start

            if self._callback:
                self._callback(
                    snap, elapsed, password,
                    success, password if success else None,
                )

            if success:
                with self._lock:
                    if not self._result:
                        self._result["password"] = password
                self._internal_stop.set()
                return

        with self._pool_lock:
            self._worker_events.pop(threading.current_thread(), None)