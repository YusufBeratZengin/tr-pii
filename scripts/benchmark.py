"""Offline 1 MB benchmark; run from the checkout with PYTHONPATH=src."""

import statistics
import time
from collections.abc import Callable

from tr_pii import fake, find, mask


def main() -> None:
    unit = (
        "Sentetik test metni; fatura INV-2026-007; tarih 22.10.2026; "
        "dummy@example.invalid; "
        + fake.tckn(seed=82)
        + "; "
        + fake.tr_iban(seed=83)
        + "; IP 2001:db8::7.\n"
    )
    text = (unit * (1_000_000 // len(unit.encode("utf-8")) + 1)).encode("utf-8")[:1_000_000]
    payload = text.decode("utf-8", errors="ignore")
    print(f"Input: {len(payload.encode('utf-8')):,} bytes; synthetic data only")
    operations: tuple[tuple[str, Callable[[str], object]], ...] = (("find", find), ("mask", mask))
    for name, operation in operations:
        timings: list[float] = []
        for _ in range(3):
            started = time.perf_counter()
            operation(payload)
            timings.append(time.perf_counter() - started)
        print(f"{name}: median {statistics.median(timings):.3f}s; max {max(timings):.3f}s")


if __name__ == "__main__":
    main()
