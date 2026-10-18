import numpy as np

from common import DATA, read_hex

from golden import load_quant, run_one


EXPECTED = {
    "weights.hex": (25408, 8, True),
    "biases.hex": (42, 16, True),
    "images.hex": (12544, 8, False),
    "labels.hex": (16, 4, False),
    "exp_hidden.hex": (512, 8, False),
    "exp_scores.hex": (160, 24, True),
    "exp_digit.hex": (16, 4, False)
}


def main():
    files = {}

    for name, (count, bits, signed) in EXPECTED.items():
        values = read_hex(
            DATA / name, bits, signed
        )

        assert len(values) == count, (
            f"{name}: Wrong number of entries"
        )

        files[name] = values

        print(f"PASS: {name} ({count} values)")

    quant = load_quant()

    original_weights = np.concatenate([
        quant["w1"].T.flatten(),
        quant["w2"].T.flatten()
    ])

    original_biases = np.concatenate([
        quant["b1"], quant["b2"]
    ])

    np.testing.assert_array_equal(
        files["weights.hex"],
        original_weights
    )

    np.testing.assert_array_equal(
        files["biases.hex"],
        original_biases
    )

    images = files["images.hex"].reshape(16, 784)

    expected_hidden = files["exp_hidden.hex"].reshape(16, 32)
    expected_scores = files["exp_scores.hex"].reshape(16, 10)
    expected_digits = files["exp_digit.hex"]

    for i in range(16):
        hidden, scores, digit, _ = run_one(
            images[i], quant
        )

        np.testing.assert_array_equal(
            hidden, expected_hidden[i]
        )

        np.testing.assert_array_equal(
            scores, expected_scores[i]
        )

        assert digit == expected_digits[i]

        print(f"Image {i}: PASS")

    print("ALL PYTHON EXPORT CHECKS PASSED")


if __name__ == "__main__":
    main()