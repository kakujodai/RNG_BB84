
"""
Workflow:
1. Use quantum-generated randomness (QRNG) for bit and basis selection in BB84.
2. Alice gets qubits and sends to Bob, who measures in random bases.
3. Alice and Bob publicly compare bases and keep only matching bits.
4. To detect eavesdropping, a random subset of the shared key is revealed and compared. If discrepancies are found, eavesdropping is detected and the key is discarded.
5. If no eavesdropping is detected, the remaining key is used for encryption/decryption of messages between Alice and Bob.
6. This ensures secure key exchange and encrypted communication.
"""

from qiskit import QuantumCircuit, Aer, execute
from rng.qrng import random_basis, qrng_bits

def bb84_protocol(num_bits):
    """
    Simulate the BB84 protocol between Alice and Bob using QRNG for basis and bit selection.
    Returns the shared secret key and protocol details. Also detects eavesdropping by comparing a random subset of the key.
    """
    # Alice generates random bits and bases
    alice_bits_and_bases = qrng_bits(num_bits)
    alice_bits = [bit for bit, _ in alice_bits_and_bases]
    alice_bases = [basis for _, basis in alice_bits_and_bases]

    # Bob generates random bases
    bob_bases = [random_basis() for _ in range(num_bits)]

    # Bob measures Alice's qubits 
    simulator = Aer.get_backend('qasm_simulator')
    bob_results = []
    for i in range(num_bits):
        qc = QuantumCircuit(1, 1)
        # Alice's bit in her basis
        if alice_bases[i] == 'X':
            qc.h(0)
        if alice_bits[i] == 1:
            qc.x(0)
        # Bob measures in his basis
        if bob_bases[i] == 'X':
            qc.h(0)
        qc.measure(0, 0)
        result = execute(qc, simulator, shots=1).result()
        measured_bit = int(list(result.get_counts().keys())[0])
        bob_results.append(measured_bit)

    # keep only bits where Alice and Bob used the same basis
    shared_key = [alice_bits[i] for i in range(num_bits) if alice_bases[i] == bob_bases[i]]
    shared_indices = [i for i in range(num_bits) if alice_bases[i] == bob_bases[i]]

    # eve detection: reveal a random subset of the shared key and compare
    import random # should we really be using random here?
    test_sample_size = max(1, len(shared_key) // 4)
    test_indices = random.sample(range(len(shared_key)), test_sample_size) if len(shared_key) > 0 else []
    alice_test_bits = [shared_key[i] for i in test_indices]
    bob_test_bits = [bob_results[shared_indices[i]] for i in test_indices]
    eavesdrop_detected = alice_test_bits != bob_test_bits
    # remove test bits from the key
    final_key = [bit for i, bit in enumerate(shared_key) if i not in test_indices]
    return final_key, shared_indices, alice_bits, alice_bases, bob_bases, bob_results, eavesdrop_detected


