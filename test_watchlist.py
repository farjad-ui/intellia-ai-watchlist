"""Run with: python test_watchlist.py"""
import sys


def run():
    tests = [v for k, v in globals().items() if k.startswith("test_")]
    for t in tests:
        t()
        print(".", end="")
    print(f"\nok ({len(tests)} tests)")


if __name__ == "__main__":
    run()
