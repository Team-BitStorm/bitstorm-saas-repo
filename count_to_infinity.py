"""Count forever using the standard library's infinite iterator."""

from itertools import count


def count_to_infinity(start: int = 0, step: int = 1) -> None:
    """Print integers from `start`, increasing by `step`, without stopping."""
    for n in count(start, step):
        print(n)


if __name__ == "__main__":
    count_to_infinity()
