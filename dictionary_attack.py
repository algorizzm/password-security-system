"""
dictionary_attack.py
Educational simulation of dictionary attacks against bcrypt-hashed passwords.
"""

import gzip
import os
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed


class DictionaryAttack:
    """
    Basic single-threaded dictionary attack.
    Tries every word in a plaintext wordlist against the target account.
    """

    def __init__(self, wordlist_file="wordlist.txt"):
        self.wordlist_file = wordlist_file
        self.wordlist = self._load_wordlist()

    def _load_wordlist(self):
        """Load words from a plain-text wordlist file."""
        try:
            with open(self.wordlist_file, "r", encoding="utf-8", errors="ignore") as f:
                return [line.strip() for line in f if line.strip()]
        except FileNotFoundError:
            return []

    def attack(self, username, login_system, callback=None, stop_event=None):
        """
        Attempt a dictionary attack on *username*.

        Args:
            username:     Target account name.
            login_system: LoginSystem instance (provides login_user()).
            callback:     Optional callable(attempts, elapsed, success, password).
            stop_event:   Optional threading.Event — set it to abort early.

        Returns:
            (success: bool, attempts: int, elapsed: float, password: str | None)
        """
        if not self.wordlist:
            return False, 0, 0.0, None

        start = time.time()
        attempts = 0

        for word in self.wordlist:
            if stop_event and stop_event.is_set():
                return False, attempts, time.time() - start, None

            attempts += 1
            success, _ = login_system.login_user(username, word)
            elapsed = time.time() - start

            if callback:
                callback(attempts, elapsed, success, word if success else None)

            if success:
                return True, attempts, elapsed, word

        return False, attempts, time.time() - start, None


class FastDictionaryAttack:
    """
    Multi-threaded dictionary attack with adjustable speed (1–10).
    Splits the wordlist across worker threads for parallel checking.

    Speed multiplier → thread count mapping:
        1 →  1,  2 →  2,  3 →  4,  4 →  6,  5 →  8,
        6 → 12,  7 → 16,  8 → 24,  9 → 32, 10 → 48
    """

    _THREAD_MAP = {1: 1, 2: 2, 3: 4, 4: 6, 5: 8,
                   6: 12, 7: 16, 8: 24, 9: 32, 10: 48}

    def __init__(self, wordlist_file="wordlist.txt", speed_multiplier=1):
        self.wordlist_file = wordlist_file
        self.speed_multiplier = max(1, min(10, speed_multiplier))
        self.wordlist = self._load_wordlist()
        self._pause_event = threading.Event()
        self._pause_event.set()   # not paused initially

    def _load_wordlist(self):
        """Load from plain .txt or gzip-compressed .gz wordlist."""
        if not os.path.exists(self.wordlist_file):
            # fallback to wordlist.txt
            alt = "wordlist.txt"
            if os.path.exists(alt):
                self.wordlist_file = alt
            else:
                return []

        try:
            if self.wordlist_file.endswith(".gz"):
                with gzip.open(self.wordlist_file, "rt", encoding="utf-8", errors="ignore") as f:
                    return [line.strip() for line in f if line.strip()]
            else:
                with open(self.wordlist_file, "r", encoding="utf-8", errors="ignore") as f:
                    return [line.strip() for line in f if line.strip()]
        except Exception:
            return []

    def set_speed(self, speed_multiplier):
        """Adjust thread count mid-attack (takes effect on next chunk)."""
        self.speed_multiplier = max(1, min(10, speed_multiplier))

    def pause(self):
        """Pause all worker threads."""
        self._pause_event.clear()

    def resume(self):
        """Resume all worker threads."""
        self._pause_event.set()

    def attack(self, username, login_system, callback=None, stop_event=None):
        """
        Multi-threaded dictionary attack.

        Returns:
            (success: bool, attempts: int, elapsed: float, password: str | None)
        """
        if not self.wordlist:
            return False, 0, 0.0, None

        start = time.time()
        n_threads = self._THREAD_MAP.get(self.speed_multiplier, 1)

        found_password = [None]
        attempts_counter = [0]
        lock = threading.Lock()
        success_flag = [False]

        def try_word(word):
            # Respect pause
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
                    callback(attempts_counter[0], elapsed, ok, word if ok else None)
                if ok:
                    success_flag[0] = True
                    found_password[0] = word

            return ok

        with ThreadPoolExecutor(max_workers=n_threads) as executor:
            futures = {executor.submit(try_word, w): w for w in self.wordlist}
            for future in as_completed(futures):
                if success_flag[0] or (stop_event and stop_event.is_set()):
                    # Cancel remaining futures
                    for f in futures:
                        f.cancel()
                    break

        elapsed = time.time() - start
        return success_flag[0], attempts_counter[0], elapsed, found_password[0]
