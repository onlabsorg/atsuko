# atsuko

A tool for easily create command-line interfaces in Python.

## Installation

Install `atsuko` using `pip`:

```bash
pip install atsuko
```

## Usage

Here's a simple example of how to use `atsuko` to create a command-line interface:

```python
import sys
from atsuko import CLI

# Create a new CLI application
app = CLI(
    name="my-app",
    description="A simple example application.",
    version="0.1.0"
)

@app.command
def greet(name: str):
    """Greets the given name."""
    app.log(f"Hello, {name}!")

if __name__ == "__main__":
    app.run(sys.argv[1:])
```

You can then run the application from the command line:

```bash
python my_app.py greet World
# Output: Hello, World!
```

## Contributing

Contributions are welcome! Please feel free to submit a pull request.

## License

This project is licensed under the Apache License 2.0. See the [LICENSE](LICENSE) file for details.
