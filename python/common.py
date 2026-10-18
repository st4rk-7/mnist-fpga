from pathlib import Path
from http.client import HTTPException
import shutil
import tempfile
import urllib.request
from zipfile import BadZipFile
import zlib
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"

MNIST_URL = (
    "https://storage.googleapis.com/"
    "tensorflow/tf-keras-datasets/mnist.npz"
)


def _read_mnist(path):
    # Read every array before closing the archive to detect damaged downloads.
    with np.load(path, allow_pickle=False) as data:
        return (
            data["x_train"],
            data["y_train"],
            data["x_test"],
            data["y_test"]
        )


def load_mnist():
    DATA.mkdir(parents=True, exist_ok=True)
    path = DATA / "mnist.npz"

    if path.exists():
        try:
            return _read_mnist(path)
        except (BadZipFile, EOFError, ValueError, KeyError, zlib.error):
            print("Cached MNIST file is incomplete or damaged. Downloading again...")

    print("Downloading MNIST dataset...")
    try:
        # Keep partial downloads separate from the cached dataset.
        with tempfile.TemporaryDirectory(prefix="mnist-download-", dir=DATA) as folder:
            temporary_path = Path(folder) / "mnist.npz"
            with urllib.request.urlopen(MNIST_URL, timeout=60) as response:
                with temporary_path.open("wb") as output:
                    shutil.copyfileobj(response, output)

            arrays = _read_mnist(temporary_path)
            temporary_path.replace(path)
            return arrays
    except (OSError, HTTPException, BadZipFile, EOFError, ValueError, KeyError, zlib.error) as error:
        raise RuntimeError(
            "Could not download a complete MNIST dataset. "
            "Check your internet connection and run the script again. "
            "The failed download was not saved as mnist.npz."
        ) from error


def pixels_uint7(images):
    images = np.asarray(images, dtype=np.uint8)

    if images.ndim == 2:
        images = images.reshape(1, 784)
    else:
        images = images.reshape(-1, 784)

    return images >> 1


def hex_twos(value, bits):
    value = int(value)

    minimum = -(1 << (bits - 1))
    maximum = (1 << (bits - 1)) - 1

    if not minimum <= value <= maximum:
        raise OverflowError("Value does not fit")

    mask = (1 << bits) - 1
    return f"{value & mask:0{bits // 4}X}"


def write_hex(path, values, bits, signed=True):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, "w") as file:
        for value in np.asarray(values).flatten():
            value = int(value)

            if signed:
                text = hex_twos(value, bits)
            else:
                if not 0 <= value < (1 << bits):
                    raise OverflowError("Unsigned value invalid")

                text = f"{value:0{bits // 4}X}"

            file.write(text + "\n")

    print("Created:", path.name)


def read_hex(path, bits, signed=True):
    values = []

    with open(path) as file:
        for line in file:
            line = line.strip()

            if not line:
                continue

            value = int(line, 16)

            if signed and value >= (1 << (bits - 1)):
                value -= (1 << bits)

            values.append(value)

    return np.array(values, dtype=np.int64)


def float_forward(pixels, weights):
    x = np.asarray(pixels, dtype=np.float32) / 127.0

    hidden = np.maximum(
        x @ weights["w1"] + weights["b1"], 0
    )

    scores = hidden @ weights["w2"] + weights["b2"]

    return scores
