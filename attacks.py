"""
attacks.py

Educational simulation of dictionary and brute-force password attacks.

Classes
-------
DictionaryAttack        — baseline, single-threaded dictionary attack
BruteForceAttack        — baseline, single-threaded brute-force (≤4 chars, lowercase only)
FastDictionaryAttack    — parallelised dictionary attack with speed_multiplier (1–10)
FastBruteForceAttack    — parallelised brute-force with speed_multiplier (1–10),
                          full charset (a-z, A-Z, 0-9, symbols), up to 8 characters
"""

import itertools
import string
import time
import threading
import queue as _queue
from typing import Callable, Optional, Tuple

# ---------------------------------------------------------------------------
# Shared constants
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
# Baseline classes  (original interface preserved exactly)
# ---------------------------------------------------------------------------

class DictionaryAttack:
    """
    Educational simulation of a dictionary attack.

    Tries every password in a wordlist file, one at a time.
    Fast against weak/common passwords; useless against random ones.
    """

    def __init__(self, wordlist_file: str = "wordlist.txt") -> None:
        self.wordlist_file = wordlist_file
        self.wordlist = self._load_wordlist()

    def _load_wordlist(self) -> list:
        try:
            with open(self.wordlist_file, "r", encoding="utf-8", errors="ignore") as fh:
                return [line.strip() for line in fh if line.strip()]
        except FileNotFoundError:
            return []

    def attack(
        self,
        username: str,
        login_system,
        callback: Optional[Callable] = None,
        stop_event: Optional[threading.Event] = None,
    ) -> Tuple[bool, int, float, Optional[str]]:
        """
        Run a single-threaded dictionary attack.

        Callback signature:
            callback(attempts, elapsed_time, success, cracked_password_or_None)
        """
        if not self.wordlist:
            return False, 0, 0.0, None

        start = time.time()
        attempts = 0

        for password in self.wordlist:
            if stop_event and stop_event.is_set():
                return False, attempts, time.time() - start, None

            attempts += 1
            success, _ = login_system.login_user(username, password)
            elapsed = time.time() - start

            if callback:
                callback(attempts, elapsed, success, password if success else None)

            if success:
                return True, attempts, elapsed, password

        return False, attempts, time.time() - start, None


class BruteForceAttack:
    """
    Educational simulation of a brute-force attack.

    INTENTIONALLY LIMITED to 4 characters and lowercase letters to illustrate
    why longer/complex passwords are exponentially harder to crack.
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
# Fast classes — parallel, shared-queue + per-worker stop events
# ---------------------------------------------------------------------------
#
# Architecture (Option A — separate control channel)
# ───────────────────────────────────────────────────
# Both fast classes share this design:
#
#   Work channel  : a queue.Queue of password candidates (never touched by
#                   resize logic — zero sentinels, zero pollution).
#
#   Control channel: a dict mapping each live Thread → its own threading.Event.
#                   set_speed() signals specific workers to stop by setting
#                   their individual event.  Workers check their own event
#                   after every bcrypt call; if set they exit cleanly without
#                   touching the queue.
#
# Resize flow (scale down 10x → 1x example)
# ──────────────────────────────────────────
#   1. set_speed(1) acquires _pool_lock.
#   2. Counts 48 live workers, target = 1, so must remove 47.
#   3. Picks 47 workers from _worker_events, sets their individual stop Event.
#   4. Releases lock immediately — no queue writes, no blocking.
#   5. Each signalled worker finishes its current bcrypt check (~250 ms),
#      sees its event is set, removes itself from _worker_events, and exits.
#   6. The 1 remaining worker continues uninterrupted from the shared queue.
#
# Producer thread (FastBruteForceAttack only)
# ────────────────────────────────────────────
# Brute-force uses a bounded queue (maxsize=512) + a dedicated producer
# thread so the generator never races ahead and exhausts RAM.
# DictionaryAttack pre-fills the queue upfront (wordlists fit in RAM easily).


class FastDictionaryAttack:
    """
    Parallelised dictionary attack with a live-resizable worker pool.

    speed_multiplier (1–10) sets the initial worker count and can be
    changed at any time via set_speed() — even while the attack is running.
    Uses a separate per-worker control channel so the work queue is never
    polluted with sentinel values.

    Callback signature (identical to DictionaryAttack):
        callback(attempts, elapsed_time, success, cracked_password_or_None)
    """

    def __init__(
        self,
        wordlist_file: str = "wordlist.txt",
        speed_multiplier: int = 1,
    ) -> None:
        self.wordlist_file = wordlist_file
        self._speed = speed_multiplier
        self.wordlist = self._load_wordlist()

        self._pool_lock = threading.Lock()
        # Maps live Thread → its individual stop Event
        self._worker_events: dict = {}
        self._internal_stop = threading.Event()

    def _load_wordlist(self) -> list:
        try:
            with open(self.wordlist_file, "r", encoding="utf-8", errors="ignore") as fh:
                return [line.strip() for line in fh if line.strip()]
        except FileNotFoundError:
            return []

    # ------------------------------------------------------------------
    def set_speed(self, speed_multiplier: int) -> None:
        """
        Resize the worker pool to match the new multiplier.
        Safe to call from any thread at any time, including mid-attack.
        Never writes to the work queue.
        """
        if not 1 <= speed_multiplier <= 10:
            return
        self._speed = speed_multiplier

        with self._pool_lock:
            if not self._worker_events:
                return  # not running — stored for next run

            target = _speed_to_workers(speed_multiplier)
            current = len(self._worker_events)

            if target > current:
                # Scale up — spin up new workers
                for _ in range(target - current):
                    stop_evt = threading.Event()
                    t = threading.Thread(
                        target=self._worker_fn, args=(stop_evt,), daemon=True
                    )
                    self._worker_events[t] = stop_evt
                    t.start()

            elif target < current:
                # Scale down — signal excess workers via their own stop event
                excess = current - target
                victims = list(self._worker_events.keys())[:excess]
                for t in victims:
                    self._worker_events[t].set()   # worker exits after current check
                    # Remove immediately; worker cleans up its own entry on exit
                    del self._worker_events[t]

    # ------------------------------------------------------------------
    def attack(
        self,
        username: str,
        login_system,
        callback: Optional[Callable] = None,
        stop_event: Optional[threading.Event] = None,
    ) -> Tuple[bool, int, float, Optional[str]]:
        if not self.wordlist:
            return False, 0, 0.0, None

        # ── shared state ──────────────────────────────────────────────
        self._q: _queue.Queue = _queue.Queue()
        self._internal_stop = threading.Event()
        self._result: dict = {}
        self._lock = threading.Lock()
        self._attempts = [0]
        self._start = time.time()
        self._username = username
        self._login_system = login_system
        self._callback = callback

        for word in self.wordlist:
            self._q.put(word)

        # Mirror external stop → set internal stop; workers notice via timeout loop
        if stop_event:
            def _watch():
                stop_event.wait()
                self._internal_stop.set()
            threading.Thread(target=_watch, daemon=True).start()

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

        # ── wait for all workers to finish ────────────────────────────
        while True:
            with self._pool_lock:
                alive = {t: e for t, e in self._worker_events.items() if t.is_alive()}
                self._worker_events = alive
                if not alive:
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
          - my_stop is set (scale-down signal from set_speed)
          - _internal_stop is set (password found or external stop)
          - queue is empty (all candidates exhausted)
        """
        while not self._internal_stop.is_set() and not my_stop.is_set():
            try:
                password = self._q.get(timeout=0.1)
            except _queue.Empty:
                break   # queue exhausted

            success, _ = self._login_system.login_user(self._username, password)

            with self._lock:
                self._attempts[0] += 1
                snap = self._attempts[0]

            elapsed = time.time() - self._start

            if self._callback:
                self._callback(snap, elapsed, success, password if success else None)

            if success:
                with self._lock:
                    if not self._result:
                        self._result["password"] = password
                self._internal_stop.set()
                return

        # Clean up own entry (may already be removed by set_speed scale-down)
        with self._pool_lock:
            self._worker_events.pop(threading.current_thread(), None)


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

    ⚠  Complexity warning — bcrypt (rounds=12) costs ~250 ms per check.
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    Even with 48 threads the effective rate is only ~190 checks/sec.

        Length 4, lowercase only  (26^4  =     456 976) ≈   40 min  at 1x
                                                         ≈    1 min  at 10x
        Length 4, full charset    (95^4  =  81 450 625) ≈  5 days   at 1x
                                                         ≈  2.5 hrs  at 10x

    Callback signature (identical to BruteForceAttack):
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

    # ------------------------------------------------------------------
    def estimate_attempts(self) -> int:
        n = len(self.charset)
        return sum(n ** l for l in range(1, self.max_length + 1))

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

        # ── producer thread ───────────────────────────────────────────
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