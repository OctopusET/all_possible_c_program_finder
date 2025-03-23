# All Possible n-Byte C Programs Finder

## Why This Project?

This project explores how small valid C programs can be. It generates random code snippets within `n` bytes, tests if they compile, and saves successful programs.

## Features

- Creates random C code of a specific size.
- Allows custom character sets.
- Tests compilability using GCC.
- Uses multiple CPU cores for faster testing.
- Saves compiled programs as `.c` files.

## How to Use

Run with default settings (5-byte code):
```
python random_c_tester.py
```

Test a specific byte size (e.g., 10 bytes):
```
python random_c_tester.py 10
```

Run unlimited tests:
```
python random_c_tester.py --tasks -1
```

Use custom characters:
```
python random_c_tester.py --charset "abc123+="
```

## How It Works

1. Generates random code using specified characters.
2. Inserts the code into a C program template.
3. Compiles the program with GCC.
4. Saves successful compilations as `.c` files.

## Saved Results

Successful programs are saved as `.c` files:
```
[PID]_[UUID].c
```

## Limits

Testing all combinations is impractical for large sizes due to exponential growth. Instead, the tool samples randomly.

## Example Output

Console output for successful compilations:
```
Compilation successful! Saved as 1234_a1b2c3d4.c
Progress: 200 attempts, 2 successes (1.00%)
```

## License

MIT License
