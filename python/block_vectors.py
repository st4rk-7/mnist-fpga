import csv

from common import DATA, read_hex


def write_csv(name, headings, rows):
    with open(DATA / name, "w", newline="") as f:
        writer = csv.writer(f)

        writer.writerow(headings)
        writer.writerows(rows)

    print("Created:", name)


def relu_clip(acc):
    return min(127, max(0, acc) >> 11)


def main():
    mac_inputs = [
        (0, 5, 10),
        (500, -3, 100),
        (-200, 7, 20),
        (-32768, 127, 127),
        (32767, -127, 127)
    ]

    mac_rows = []

    for bias, weight, pixel in mac_inputs:
        result = bias + weight * pixel

        mac_rows.append(
            (bias, weight, pixel, result)
        )

    write_csv(
        "mac_vectors.csv",
        ["bias", "weight", "pixel", "expected_acc"],
        mac_rows
    )

    accumulators = [
        -5000, -1, 0, 2047,
        2048, 100000, 300000
    ]

    relu_rows = [
        (acc, relu_clip(acc))
        for acc in accumulators
    ]

    write_csv(
        "relu_vectors.csv",
        ["acc", "expected_hidden"],
        relu_rows
    )

    examples = [
        [0, 10, 1, 2, 3, 4, 5, 6, 7, 8],
        [-100, -20, -30, -40, -1,
         -2, -3, -4, -5, -6],
        [5, 5, 5, 2, 1, 0, -1, -2, -3, -4]
    ]

    argmax_rows = []

    for scores in examples:
        digit = max(
            range(10),
            key=lambda i: scores[i]
        )

        argmax_rows.append(
            scores + [digit]
        )

    write_csv(
        "argmax_vectors.csv",
        [f"score_{i}" for i in range(10)]
        + ["expected_digit"],
        argmax_rows
    )

    weights = read_hex(
        DATA / "weights.hex", 8
    )

    biases = read_hex(
        DATA / "biases.hex", 16
    )

    pixels = read_hex(
        DATA / "images.hex", 8,
        signed=False
    )

    accumulator = int(biases[0])
    rows = []

    for i in range(784):
        weight = int(weights[i])
        pixel = int(pixels[i])

        accumulator += weight * pixel

        rows.append((
            i, weight, pixel, accumulator
        ))

    write_csv(
        "mac_784_example.csv",
        ["index", "weight", "pixel", "expected_acc"],
        rows
    )

    print("PASS: Test vectors created")


if __name__ == "__main__":
    main()