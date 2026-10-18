import json
import numpy as np

from common import (
    DATA,
    load_mnist,
    pixels_uint7,
    write_hex
)

from golden import (
    load_quant,
    run_one,
    vectorized_inference
)


LABEL_ORDER = [
    0, 1, 2, 3,
    4, 5, 6, 7,
    8, 9, 1, 4,
    9, 0, 9, 0
]


def choose_16(labels, predictions):
    indices = []
    used = set()

    for position, label in enumerate(LABEL_ORDER):

        desired = 6 if position == 5 else label

        matches = np.flatnonzero(
            (labels == label)
            & (predictions == desired)
        )

        if position == 5 and len(matches) == 0:
            matches = np.flatnonzero(
                (labels == label)
                & (predictions == label)
            )

        available = [
            int(i) for i in matches
            if int(i) not in used
        ]

        if not available:
            raise RuntimeError(
                f"No suitable image for digit {label}"
            )

        selected = available[0]

        indices.append(selected)
        used.add(selected)

    return indices


def main():
    _, _, x_test, y_test = load_mnist()

    quant = load_quant()

    pixels = pixels_uint7(x_test)

    _, _, predictions = vectorized_inference(
        pixels, quant
    )

    indices = choose_16(
        y_test, predictions
    )

    selected_images = pixels[indices]
    selected_labels = y_test[indices]

    hidden_results = []
    score_results = []
    digit_results = []

    largest_acc = 0

    for image in selected_images:
        hidden, scores, digit, max_acc = run_one(
            image, quant
        )

        hidden_results.extend(hidden.tolist())
        score_results.extend(scores.tolist())
        digit_results.append(digit)

        largest_acc = max(largest_acc, max_acc)

    # Hardware weights are stored neuron by neuron.
    weights = np.concatenate([
        quant["w1"].T.flatten(),
        quant["w2"].T.flatten()
    ])

    biases = np.concatenate([
        quant["b1"],
        quant["b2"]
    ])

    write_hex(
        DATA / "weights.hex",
        weights, 8
    )

    write_hex(
        DATA / "biases.hex",
        biases, 16
    )

    write_hex(
        DATA / "images.hex",
        selected_images, 8,
        signed=False
    )

    write_hex(
        DATA / "labels.hex",
        selected_labels, 4,
        signed=False
    )

    write_hex(
        DATA / "exp_hidden.hex",
        hidden_results, 8,
        signed=False
    )

    write_hex(
        DATA / "exp_scores.hex",
        score_results, 24
    )

    write_hex(
        DATA / "exp_digit.hex",
        digit_results, 4,
        signed=False
    )

    with open(DATA / "selected_indices.json", "w") as f:
        json.dump(indices, f, indent=2)

    print("Expected digits:", digit_results)

    print("Largest accumulator:", largest_acc)

    print("PASS: Hex files exported")


if __name__ == "__main__":
    main()