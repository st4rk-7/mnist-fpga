import argparse
import numpy as np

from common import DATA, load_mnist, pixels_uint7

ACC_MIN = -(1 << 23)
ACC_MAX = (1 << 23) - 1


def load_quant():
    with np.load(DATA / "quant_model.npz") as data:
        return {
            key: data[key]
            for key in ("w1", "b1", "w2", "b2")
        }


def vectorized_inference(pixels, quant):
    x = np.asarray(pixels, dtype=np.int64)

    if x.ndim == 1:
        x = x.reshape(1, 784)

    acc1 = (
        x @ quant["w1"].astype(np.int64)
        + quant["b1"].astype(np.int64)
    )

    hidden = np.clip(
        np.maximum(acc1, 0) >> 11,
        0,
        127
    ).astype(np.uint8)

    scores = (
        hidden.astype(np.int64)
        @ quant["w2"].astype(np.int64)
        + quant["b2"].astype(np.int64)
    )

    digit = np.argmax(
        scores, axis=1
    ).astype(np.uint8)

    return hidden, scores, digit


def run_one(pixels, quant):
    x = np.asarray(
        pixels, dtype=np.int64
    ).reshape(784)

    hidden = []
    scores = []

    max_abs = 0

    for neuron in range(32):
        accumulator = int(quant["b1"][neuron])

        max_abs = max(max_abs, abs(accumulator))

        for i in range(784):
            weight = int(quant["w1"][i, neuron])
            pixel = int(x[i])

            accumulator += weight * pixel

            max_abs = max(
                max_abs, abs(accumulator)
            )

            if not ACC_MIN <= accumulator <= ACC_MAX:
                raise OverflowError(
                    "Layer 1 accumulator overflow"
                )

        output = min(
            127,
            max(0, accumulator) >> 11
        )

        hidden.append(output)

    for neuron in range(10):
        accumulator = int(quant["b2"][neuron])

        max_abs = max(max_abs, abs(accumulator))

        for i in range(32):
            weight = int(quant["w2"][i, neuron])

            accumulator += weight * hidden[i]

            max_abs = max(
                max_abs, abs(accumulator)
            )

            if not ACC_MIN <= accumulator <= ACC_MAX:
                raise OverflowError(
                    "Layer 2 accumulator overflow"
                )

        scores.append(accumulator)

    predicted_digit = max(
        range(10),
        key=lambda i: scores[i]
    )

    return (
        np.array(hidden, dtype=np.uint8),
        np.array(scores, dtype=np.int64),
        predicted_digit,
        max_abs
    )


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--test-index", type=int, default=0
    )

    args = parser.parse_args()

    _, _, x_test, y_test = load_mnist()

    quant = load_quant()

    pixels = pixels_uint7(x_test)

    hidden, scores, digit, max_acc = run_one(
        pixels[args.test_index],
        quant
    )

    fast_hidden, fast_scores, fast_digit = (
        vectorized_inference(
            pixels[args.test_index], quant
        )
    )

    assert np.array_equal(
        hidden, fast_hidden[0]
    )

    assert np.array_equal(
        scores, fast_scores[0]
    )

    assert digit == int(fast_digit[0])

    print("Correct digit:", y_test[args.test_index])

    print("Predicted digit:", digit)

    print("32 hidden values:")
    print(hidden)

    print("10 output scores:")
    print(scores)

    print("Largest accumulator:", max_acc)

    print("PASS: Both Python methods match")


if __name__ == "__main__":
    main()