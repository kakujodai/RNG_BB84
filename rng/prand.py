import random

def main():
    seed = input("Enter a seed for the pseudo-random generator: ")
    try:
        seed_int = int(seed)
    except ValueError:
        seed_int = hash(seed)
    random.seed(seed_int)
    number = random.randint(0, 2**32 - 1)
    print(f"Seed used: {seed_int}")
    print(f"Pseudo-random number: {number}")

if __name__ == "__main__":
    main()
    