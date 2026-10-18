import argparse
import numpy as np

from common import DATA, load_mnist, pixels_uint7


def evaluate(x, labels, params):
    correct = 0

    for start in range(0, len(x), 1024):
        xb = x[start:start + 1024]

        hidden = np.maximum(
            xb @ params["w1"] + params["b1"], 0
        )

        scores = hidden @ params["w2"] + params["b2"]

        predictions = np.argmax(scores, axis=1)

        correct += np.count_nonzero(
            predictions == labels[start:start + 1024]
        )

    return correct / len(x)


def train(x, y, x_test, y_test, epochs=18):
    rng = np.random.default_rng(42)

    params = {
        "w1": (
            rng.standard_normal((784, 32))
            * np.sqrt(2 / 784)
        ).astype(np.float32),

        "b1": np.zeros(32, dtype=np.float32),

        "w2": (
            rng.standard_normal((32, 10))
            * np.sqrt(2 / 32)
        ).astype(np.float32),

        "b2": np.zeros(10, dtype=np.float32)
    }

    momentum = {
        k: np.zeros_like(v) for k, v in params.items()
    }

    velocity = {
        k: np.zeros_like(v) for k, v in params.items()
    }

    step = 0
    batch_size = 128
    learning_rate = 0.001

    for epoch in range(epochs):
        indices = rng.permutation(len(x))

        for start in range(0, len(x), batch_size):
            ids = indices[start:start + batch_size]

            xb = x[ids]
            targets = y[ids]

            z1 = xb @ params["w1"] + params["b1"]
            hidden = np.maximum(z1, 0)

            logits = hidden @ params["w2"] + params["b2"]

            probabilities = np.exp(
                logits - logits.max(axis=1, keepdims=True)
            )

            probabilities /= probabilities.sum(
                axis=1, keepdims=True
            )

            probabilities[
                np.arange(len(ids)), targets
            ] -= 1

            probabilities /= len(ids)

            gradients = {
                "w2": hidden.T @ probabilities,
                "b2": probabilities.sum(axis=0)
            }

            dh = (
                probabilities @ params["w2"].T
            ) * (z1 > 0)

            gradients["w1"] = xb.T @ dh
            gradients["b1"] = dh.sum(axis=0)

            step += 1

            for name, grad in gradients.items():
                momentum[name] = (
                    0.9 * momentum[name] + 0.1 * grad
                )

                velocity[name] = (
                    0.999 * velocity[name]
                    + 0.001 * grad * grad
                )

                m = momentum[name] / (1 - 0.9 ** step)
                v = velocity[name] / (1 - 0.999 ** step)

                params[name] -= learning_rate * m / (
                    np.sqrt(v) + 1e-8
                )

        accuracy = evaluate(x[:5000], y[:5000], params)

        print(
            f"Epoch {epoch + 1}/{epochs}"
            f" - Training accuracy: {accuracy:.2%}",
            flush=True
        )

    final_accuracy = evaluate(
        x_test, y_test, params
    )

    print(
        f"Final test accuracy: {final_accuracy:.2%}"
    )

    return params


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--epochs", type=int, default=18
    )

    args = parser.parse_args()

    x_train, y_train, x_test, y_test = load_mnist()

    x_train = (
        pixels_uint7(x_train).astype(np.float32) / 127
    )

    x_test = (
        pixels_uint7(x_test).astype(np.float32) / 127
    )

    print("Training started...")

    params = train(
        x_train,
        y_train,
        x_test,
        y_test,
        epochs=args.epochs
    )

    DATA.mkdir(parents=True, exist_ok=True)

    np.savez(
        DATA / "float_model.npz",
        **params
    )

    print("Model saved: data/float_model.npz")


if __name__ == "__main__":
    main()