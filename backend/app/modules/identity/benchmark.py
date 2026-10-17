"""Run only after changed-exposure approval; emit timing/resource numbers, no tokens."""

import asyncio
import json
import resource
from statistics import median
from time import perf_counter

from app.modules.identity.security import Passwords, random_token
from app.modules.identity.settings import AuthSettings


async def measure() -> None:
    settings = AuthSettings()
    passwords = Passwords(settings)
    timings = []
    for _ in range(5):
        value = random_token()
        start = perf_counter()
        encoded = await passwords.hash(value)
        assert await passwords.verify(value, encoded)
        timings.append((perf_counter() - start) * 1000)
    print(
        json.dumps(
            {
                "argon2_memory_kib": 65536,
                "iterations": 3,
                "parallelism": 1,
                "hash_concurrency_per_worker": settings.hash_concurrency,
                "samples": len(timings),
                "hash_plus_verify_median_ms": median(timings),
                "process_peak_rss_kib_linux": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
            }
        )
    )


if __name__ == "__main__":
    asyncio.run(measure())
