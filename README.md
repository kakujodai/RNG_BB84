# Salisbury University | MATH 490 | Quantum Computing 
***Developers: Lilly Ngo & Layla Phipps***

## Course Overview

**MATH 490 - Special Topics** 

This course enables study in specialized areas such as complex variables, logic, non-Euclidean geometry, or other topics suggested by faculty or students. Our focus this semester is **Quantum Computing**.

### Project Assignment

We were tasked with selecting a problem and its solution directly related to quantum computing to present to the class. This project explores the BB84 quantum key distribution protocol and compares quantum random number generation (QRNG) versus pseudorandom number generation (PRNG) in the context of quantum cryptography security.

---

## Project Overview

This project implements the **BB84 quantum key distribution protocol** with real quantum random number generation using IBM Quantum hardware. The demonstration explores:

- **BB84 Protocol**: Quantum key exchange between Alice and Bob
- **Quantum vs. Classical Randomness**: Comparison of QRNG (real IBM quantum backend) vs. PRNG (pseudorandom)
- **Eavesdropping Detection**: Implementation of various Eve attack strategies:
  - Measure-and-resend attack
  - Intercept-and-replace attack
  - Cloned-state attack (demonstrates no-cloning theorem)
- **Quantum Encryption**: Using the shared quantum key to encrypt/decrypt messages

### Key Features

- Real quantum random number generation via IBM Quantum (`ibm_kingston` backend)  
- Interactive step-by-step demonstration mode  
- Comparative analysis mode (QRNG vs PRNG across attack types)  
- Eavesdropping detection through basis reconciliation  
- Unit tests for encryption and attack detection

---

## Setup Instructions

### Prerequisites

- Python 3.8+
- IBM Quantum account (free at [quantum.ibm.com](https://quantum.ibm.com))

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd RNG_BB84
   ```

2. **Create virtual environment**
   ```bash
   python -m venv .venv
   .venv\Scripts\activate  # Windows
   # or
   source .venv/bin/activate  # Mac/Linux
   ```

3. **Install dependencies**
   ```bash
   pip install qiskit qiskit-ibm-runtime
   ```

4. **Configure IBM Quantum credentials**
   
   Create a `.env` file in the project root:
   ```
   IBM_TOKEN=your_ibm_quantum_token_here
   ```
   
   Get your token from [quantum.ibm.com](https://quantum.ibm.com)

---

## How to Run

### Main Presentation Demo

```bash
python presentation_demo.py
```

This interactive demo offers two modes:

**Mode 1: Step-by-Step Demo**
- Shows Alice's random bits and bases
- Displays Eve's intercept attempts and accuracy
- Shows Bob's measurements and basis reconciliation
- Detects eavesdropping through sampling
- Encrypts/decrypts a message using the shared key

**Mode 2: QRNG vs PRNG Comparison**
- Runs multiple trials comparing quantum vs. pseudorandom generation
- Tests all Eve attack types
- Generates statistical comparison tables
- Optional compromised-seed scenario

### Legacy Demo

```bash
python demo.py
```

Basic demonstration without the presentation formatting.

### Individual Components

**Test QRNG only:**
```bash
python rng/qrng.py
```

**Test PRNG only:**
```bash
python rng/prand.py
```

### Run Unit Tests

```bash
# All tests
python -m unittest

# Encryption tests only
python -m unittest tests/test_encryption.py

# Eve attack tests only
python -m unittest tests/test_eve_attacks.py
```

---

## Project Structure

```
RNG_BB84/
├── presentation_demo.py    # Main interactive demo (use this!)
├── demo.py                 # Legacy demo
├── README.md               # This file
├── workflow.txt            # Development notes
│
├── functions/              # BB84 protocol components
│   ├── bb84.py            # Core BB84 protocol implementation
│   ├── alice.py           # Alice's key generation & encryption
│   ├── bob.py             # Bob's measurement & decryption
│   └── eve.py             # Eavesdropping attack strategies
│
├── rng/                   # Random number generation
│   ├── qrng.py            # Quantum RNG (IBM backend)
│   └── prand.py           # Pseudorandom RNG
│
├── tests/                 # Unit tests
│   ├── test_encryption.py        # Encryption/decryption tests
│   └── test_eve_attacks.py       # Attack detection tests
│
└── results/               # Output files
    ├── simulation_output.txt     # Demo results
    └── comparison_simulation.txt # Comparison results
```

---

## How It Works

### BB84 Protocol Steps

1. **Alice generates random bits and bases** (Z or X)
2. **Alice encodes qubits** according to her bits and bases
3. **Eve may intercept** (depending on attack mode)
4. **Bob measures qubits** using random bases
5. **Basis reconciliation** (Alice and Bob compare bases publicly)
6. **Sifted key** created from matching bases
7. **Eavesdropping check** by comparing a sample of the key
8. **Final key** used for encryption if no eavesdropping detected

### QRNG vs PRNG

- **QRNG**: Uses real quantum measurements from IBM hardware - truly random, unpredictable
- **PRNG**: Uses deterministic algorithms - predictable if seed is known

The demonstration shows how PRNG vulnerability (seed compromise) can allow Eve to predict Alice's bases, making attacks undetectable.

---

## Sample Output

```
BB84 LIVE PRESENTATION DEMO
==========================================================================

Enter number of photons/bits to send: 8
Randomness type? AKA qrng or prng [qrng]: 
Choose Eve attack [none | measure-and-resend | intercept-and-replace | cloned-state] [measure-and-resend]: 
Generating quantum random numbers.. ✓

[ALICE] Random generation
- Alice bits (first 24):   1 0 1 1 0 1 0 1
- Alice bases (first 24):  Z X Z X Z X X Z

[EVE] Intercept/read summary
- Eve bases (first 24):     X Z X Z X Z Z X
- Eve read bits (first 24): 1 0 1 1 0 1 0 1
- Eve basis accuracy:       50.00%
- Eve bit-read accuracy:    75.00%

[BOB] Measurement summary
- Bob bases (first 24):      Z X X Z Z X X Z
- Bob measured bits (first 24): 1 0 1 0 0 1 0 1

[SIFT + TEST]
- Basis matches: 4/8
- Eavesdrop detected: YES
```

---

## References

- [BB84 Protocol](https://en.wikipedia.org/wiki/BB84)
- [Qiskit IBM Runtime Documentation](https://docs.quantum.ibm.com/api/qiskit-ibm-runtime)
- [Quantum Key Distribution Overview](https://en.wikipedia.org/wiki/Quantum_key_distribution)

---

## License

Academic project for MATH 490 - Salisbury University


