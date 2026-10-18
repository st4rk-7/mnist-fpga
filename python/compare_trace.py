import argparse
import csv

from common import DATA, read_hex


def expected_values():
    hidden = read_hex(
        DATA / "exp_hidden.hex", 8,
        signed=False
    ).reshape(16, 32)

    scores = read_hex(
        DATA / "exp_scores.hex", 24
    ).reshape(16, 10)

    digits = read_hex(
        DATA / "exp_digit.hex", 4,
        signed=False
    )

    expected = {}

    for image in range(16):

        for i in range(32):
            expected[(image, "hidden", i)] = int(
                hidden[image, i]
            )

        for i in range(10):
            expected[(image, "score", i)] = int(
                scores[image, i]
            )

        expected[(image, "digit", 0)] = int(
            digits[image]
        )

    return expected


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument("trace_csv")

    args = parser.parse_args()

    expected = expected_values()
    seen = set()

    with open(args.trace_csv, newline="") as f:
        reader = csv.DictReader(f)

        for row in reader:
            key = (
                int(row["image"]),
                row["kind"].strip(),
                int(row["index"])
            )

            actual = int(row["value"])

            if key not in expected:
                raise AssertionError(
                    f"Unexpected result: {key}"
                )

            if key in seen:
                raise AssertionError(
                    f"Duplicate result: {key}"
                )

            seen.add(key)

            if actual != expected[key]:
                print("FAIL!")
                print("Location:", key)
                print("Hardware:", actual)
                print("Python:", expected[key])
                return

    missing = set(expected) - seen

    if missing:
        print("FAIL: Some values are missing")
        print("First missing:", sorted(missing)[0])
        return

    print("PASS: ALL HARDWARE VALUES MATCH PYTHON")
    print("Checked values:", len(seen))


if __name__ == "__main__":
    main()