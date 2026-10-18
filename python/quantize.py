import numpy as np

from common import (
    DATA,
    load_mnist,
    pixels_uint7,
    float_forward
)

from golden import vectorized_inference


HIDDEN_SHIFT = 11

HIDDEN_SCALES = (
    3, 4, 5, 6, 8, 10,
    12, 16, 20, 24, 32, 40
)

SCORE_SCALES = (
    128, 256, 384, 512, 768,
    1024, 1536, 2048, 3072, 4096
)


def make_quant(params, hidden_scale, score_scale):
    factor = 1 << HIDDEN_SHIFT

    q_w1 = np.rint(
        params["w1"].astype(np.float64)
        * factor * hidden_scale / 127
    ).astype(np.int64)

    q_b1 = np.rint(
        params["b1"].astype(np.float64)
        * factor * hidden_scale
    ).astype(np.int64)

    q_w2 = np.rint(
        params["w2"].astype(np.float64)
        * score_scale / hidden_scale
    ).astype(np.int64)

    q_b2 = np.rint(
        params["b2"].astype(np.float64)
        * score_scale
    ).astype(np.int64)

    for weights in (q_w1, q_w2):
        if np.any(weights < -127) or np.any(weights > 127):
            return None

    for biases in (q_b1, q_b2):
        if np.any(biases < -32768) or np.any(biases > 32767):
            return None

    return {
        "w1": q_w1.astype(np.int8),
        "b1": q_b1.astype(np.int16),
        "w2": q_w2.astype(np.int8),
        "b2": q_b2.astype(np.int16)
    }


def main():
    with np.load(DATA / "float_model.npz") as data:
        params = {
            key: data[key]
            for key in ("w1", "b1", "w2", "b2")
        }

    x_train, y_train, x_test, y_test = load_mnist()

    calibration_pixels = pixels_uint7(
        x_train[:1200]
    )

    calibration_labels = y_train[:1200]

    best_accuracy = -1
    best_model = None

    for hidden_scale in HIDDEN_SCALES:
        for score_scale in SCORE_SCALES:

            quant = make_quant(
                params,
                hidden_scale,
                score_scale
            )

            if quant is None:
                continue

            _, _, predictions = vectorized_inference(
                calibration_pixels,
                quant
            )

            accuracy = np.mean(
                predictions == calibration_labels
            )

            if accuracy > best_accuracy:
                best_accuracy = accuracy
                best_model = (
                    hidden_scale,
                    score_scale,
                    quant
                )

    if best_model is None:
        raise RuntimeError(
            "No valid quantization found"
        )

    hidden_scale, score_scale, quant = best_model

    test_pixels = pixels_uint7(x_test)

    _, _, int_predictions = vectorized_inference(
        test_pixels, quant
    )

    integer_accuracy = np.mean(
        int_predictions == y_test
    )

    float_scores = float_forward(
        test_pixels, params
    )

    float_accuracy = np.mean(
        np.argmax(float_scores, axis=1) == y_test
    )

    np.savez(
        DATA / "quant_model.npz",
        **quant,
        hidden_scale=hidden_scale,
        score_scale=score_scale
    )

    print("Selected hidden scale:", hidden_scale)
    print("Selected score scale:", score_scale)

    print(
        f"Floating-point accuracy: {float_accuracy:.2%}"
    )

    print(
        f"8-bit integer accuracy: {integer_accuracy:.2%}"
    )

    if integer_accuracy > 0.95:
        print("PASS: Accuracy is above 95%")
    else:
        print("NOT YET PASS: Improve model accuracy")

    print("Saved: data/quant_model.npz")


if __name__ == "__main__":
    main()