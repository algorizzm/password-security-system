"""
dictionary_attack.py

Educational simulation of dictionary-based password attacks.

Classes
-------
DictionaryAttack        — baseline, single-threaded dictionary attack
FastDictionaryAttack    — parallelised dictionary attack with live-resizable
                          worker pool and speed_multiplier (1–10).
                          Streams rockyou.txt.gz (or any .txt/.gz wordlist)
                          line-by-line — no full pre-load into RAM.

Architecture (FastDictionaryAttack)
────────────────────────────────────
Work channel   : queue.Queue(maxsize=512) — producer streams the file into
                 the queue; workers drain it.  The queue is NEVER written to
                 by resize or stop logic — zero sentinel pollution.

Control channel: dict mapping each live Thread → its own threading.Event.
                 set_speed() signals specific workers to stop by setting
                 their individual event; workers exit after their current
                 bcrypt check without touching the queue.

Pause gate     : a single threading.Event shared by all workers.
                 pause() clears it (workers block at .wait());
                 resume() sets it (all workers unblock simultaneously).
"""

import gzip
import time
import threading
import queue as _queue
from typing import Callable, Optional, Tuple


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

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
# DictionaryAttack — baseline, single-threaded
# ---------------------------------------------------------------------------

class DictionaryAttack:
    """
    Educational simulation of a dictionary attack.

    Tries every password in a wordlist file, one at a time.
    Fast against weak/common passwords; useless against random ones.
    Supports plain .txt and gzipped .gz wordlists.
    """

    def __init__(self, wordlist_file: str = "wordlist.txt") -> None:
        self.wordlist_file = wordlist_file
        self.wordlist = self._load_wordlist()

    def _load_wordlist(self) -> list:
        try:
            if self.wordlist_file.endswith(".gz"):
                with gzip.open(self.wordlist_file, "rt", encoding="utf-8", errors="ignore") as fh:
                    return [line.strip() for line in fh if line.strip()]
            else:
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


# ---------------------------------------------------------------------------
# FastDictionaryAttack — parallelised, streaming, live-resizable pool
# ---------------------------------------------------------------------------

class FastDictionaryAttack:
    """
    Parallelised dictionary attack with a live-resizable worker pool.

    Streams the wordlist line-by-line from disk (plain .txt or .gz) via a
    dedicated producer thread into a bounded queue — no full pre-load into
    RAM.  RockYou-sized files (~14M lines, ~150 MB uncompressed) start
    instantly and consume only ~1 MB of memory regardless of file size.

    speed_multiplier (1–10) sets the initial worker count and can be
    changed at any time via set_speed() — even while the attack is running.
    Uses a separate per-worker control channel so the work queue is never
    polluted with sentinel values.

    Callback signature:
        callback(attempts, elapsed_time, success, cracked_password_or_None)
    """

    def __init__(
        self,
        wordlist_file: str = "rockyou.txt.gz",
        speed_multiplier: int = 1,
    ) -> None:
        self.wordlist_file = wordlist_file
        self._speed = speed_multiplier

        self._pool_lock = threading.Lock()
        # Maps live Thread → its individual stop Event
        self._worker_events: dict = {}
        self._internal_stop = threading.Event()
        # Pause gate — set means running, cleared means paused
        self._pause_event = threading.Event()
        self._pause_event.set()  # unpaused by default

    def _open_wordlist(self):
        """Return an open file handle for the wordlist (plain or gzipped)."""
        if self.wordlist_file.endswith(".gz"):
            return gzip.open(self.wordlist_file, "rt", encoding="utf-8", errors="ignore")
        return open(self.wordlist_file, "r", encoding="utf-8", errors="ignore")

    # ------------------------------------------------------------------
    def pause(self) -> None:
        """Block all workers after their current bcrypt check completes."""
        self._pause_event.clear()

    def resume(self) -> None:
        """Unblock all paused workers."""
        self._pause_event.set()

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
                    del self._worker_events[t]

    # ------------------------------------------------------------------
    def attack(
        self,
        username: str,
        login_system,
        callback: Optional[Callable] = None,
        stop_event: Optional[threading.Event] = None,
    ) -> Tuple[bool, int, float, Optional[str]]:
        try:
            self._open_wordlist().close()  # existence check before spinning up threads
        except FileNotFoundError:
            return False, 0, 0.0, None

        # ── shared state ──────────────────────────────────────────────
        # Bounded queue — producer streams ahead by at most 512 lines,
        # keeping memory flat regardless of wordlist size.
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

        # Mirror external stop
        if stop_event:
            def _watch():
                stop_event.wait()
                self._internal_stop.set()
            threading.Thread(target=_watch, daemon=True).start()

        # ── producer thread — streams file into bounded queue ─────────
        producer_done = threading.Event()

        def producer():
            try:
                with self._open_wordlist() as fh:
                    for line in fh:
                        if self._internal_stop.is_set():
                            return
                        word = line.strip()
                        if not word:
                            continue
                        # Block if queue is full — throttles to worker speed
                        while not self._internal_stop.is_set():
                            try:
                                self._q.put(word, timeout=0.1)
                                break
                            except _queue.Full:
                                continue
            finally:
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
          - my_stop is set (scale-down signal from set_speed)
          - _internal_stop is set (password found or external stop)
          - queue is empty (all candidates exhausted)
        """
        while not self._internal_stop.is_set() and not my_stop.is_set():
            # Block here while paused; wake immediately when resumed
            self._pause_event.wait()
            if self._internal_stop.is_set() or my_stop.is_set():
                break

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