"""
brute_force_attack.py
Educational simulation of brute-force attacks against bcrypt-hashed passwords.
Intentionally limited to 4-character passwords for demo purposes.
"""

import itertools
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed


# Default character set — lowercase letters only for speed in demos
DEFAULT_CHARSET = "abcdefghijklmnopqrstuvwxyz"


class BruteForceAttack:
    """
    Basic single-threaded brute-force attack.
    Tries every combination up to *max_length* characters.
    Capped at 4 characters for educational purposes.
    """

    def __init__(self, max_length=4, charset=DEFAULT_CHARSET):
        if max_length > 4:
            raise ValueError("Brute-force limited to 4 characters for educational purposes.")
        self.max_length = max_length
        self.charset = charset

    def estimate_attempts(self):
        """Total combinations that will be tried."""
        return sum(len(self.charset) ** l for l in range(1, self.max_length + 1))

    def attack(self, username, login_system, callback=None, stop_event=None):
        """
        Attempt a brute-force attack on *username*.

        Args:
            username:     Target account name.
            login_system: LoginSystem instance.
            callback:     Optional callable(attempts, elapsed, current, success, password).
            stop_event:   Optional threading.Event — set it to abort early.

        Returns:
            (success: bool, attempts: int, elapsed: float, password: str | None)
        """
        start = time.time()
        attempts = 0

        for length in range(1, self.max_length + 1):
            for combo in itertools.product(self.charset, repeat=length):
                if stop_event and stop_event.is_set():
                    return False, attempts, time.time() - start, None

                word = "".join(combo)
                attempts += 1
                success, _ = login_system.login_user(username, word)
                elapsed = time.time() - start

                if callback:
                    callback(attempts, elapsed, word, success, word if success else None)

                if success:
                    return True, attempts, elapsed, word

        return False, attempts, time.time() - start, None


class FastBruteForceAttack:
    """
    Multi-threaded brute-force attack with adjustable speed (1–10).
    Still capped at 4 characters — bcrypt makes anything longer impractical.

    Speed multiplier → thread count mapping:
        1 →  1,  2 →  2,  3 →  4,  4 →  6,  5 →  8,
        6 → 12,  7 → 16,  8 → 24,  9 → 32, 10 → 48
    """

    _THREAD_MAP = {1: 1, 2: 2, 3: 4, 4: 6, 5: 8,
                   6: 12, 7: 16, 8: 24, 9: 32, 10: 48}

    def __init__(self, max_length=4, charset=DEFAULT_CHARSET, speed_multiplier=1):
        if max_length > 4:
            raise ValueError("Brute-force limited to 4 characters for educational purposes.")
        self.max_length = max_length
        self.charset = charset
        self.speed_multiplier = max(1, min(10, speed_multiplier))
        self._pause_event = threading.Event()
        self._pause_event.set()   # not paused initially

    def set_speed(self, speed_multiplier):
        """Adjust thread count mid-attack."""
        self.speed_multiplier = max(1, min(10, speed_multiplier))

    def pause(self):
        """Pause all worker threads."""
        self._pause_event.clear()

    def resume(self):
        """Resume all worker threads."""
        self._pause_event.set()

    def estimate_attempts(self):
        """Total combinations that will be tried."""
        return sum(len(self.charset) ** l for l in range(1, self.max_length + 1))

    def _generate_candidates(self):
        """Yield every candidate string up to max_length."""
        for length in range(1, self.max_length + 1):
            for combo in itertools.product(self.charset, repeat=length):
                yield "".join(combo)

    def attack(self, username, login_system, callback=None, stop_event=None):
        """
        Multi-threaded brute-force attack.

        Returns:
            (success: bool, attempts: int, elapsed: float, password: str | None)
        """
        start = time.time()
        n_threads = self._THREAD_MAP.get(self.speed_multiplier, 1)

        found_password = [None]
        attempts_counter = [0]
        lock = threading.Lock()
        success_flag = [False]

        def try_word(word):
            self._pause_event.wait()

            if stop_event and stop_event.is_set():
                return False
            if success_flag[0]:
                return False

            ok, _ = login_system.login_user(username, word)

            with lock:
                attempts_counter[0] += 1
                elapsed = time.time() - start
                if callback:
                    callback(attempts_counter[0], elapsed, word, ok, word if ok else None)
                if ok:
                    success_flag[0] = True
                    found_password[0] = word

            return ok

        candidates = list(self._generate_candidates())

        with ThreadPoolExecutor(max_workers=n_threads) as executor:
            futures = {executor.submit(try_word, w): w for w in candidates}
            for future in as_completed(futures):
                if success_flag[0] or (stop_event and stop_event.is_set()):
                    for f in futures:
                        f.cancel()
                    break

        elapsed = time.time() - start
        return success_flag[0], attempts_counter[0], elapsed, found_password[0]
