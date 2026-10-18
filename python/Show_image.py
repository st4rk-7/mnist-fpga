from common import load_mnist, pixels_uint7

x_train, y_train, x_test, y_test = load_mnist()

print("Training images:", len(x_train))
print("Testing images:", len(x_test))

image = x_train[0]
label = y_train[0]

print("Correct digit:", label)
print("Image size:", image.shape)

pixels = pixels_uint7(image)[0].reshape(28, 28)

print("Pixel values:")
print(pixels)

print("Simple digit preview:")

for row in pixels:
    print(
        "".join(
            "##" if pixel >= 32 else "  "
            for pixel in row
        )
    )