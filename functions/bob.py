"""
Bob's role in the BB84 quantum key distribution protocol.
Bob receives qubits from Alice and measures them in random bases.
"""

from rng.qrng import random_basis
from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator


def measure_qubit(alice_bit, alice_basis, bob_basis):
    """
    Measure a single qubit using Qiskit simulator.
    
    Args:
        alice_bit (int): The bit Alice prepared (0 or 1)
        alice_basis (str): The basis Alice used ('Z' or 'X')
        bob_basis (str): The basis Bob uses for measurement ('Z' or 'X')
    
    Returns:
        int: The measured bit (0 or 1)
    """
    simulator = AerSimulator()
    qc = QuantumCircuit(1, 1)
    
    # Encode bit first, then rotate basis.
    # For X-basis, bit=1 must become |->, which is H(X|0>). 
    if alice_bit == 1:
        qc.x(0)
    if alice_basis == 'X':
        qc.h(0)
    
    # Bob measures in his basis
    if bob_basis == 'X':
        qc.h(0)
    
    qc.measure(0, 0)
    compiled = transpile(qc, simulator)
    result = simulator.run(compiled, shots=1).result()
    measured_bit = int(list(result.get_counts().keys())[0])
    return measured_bit


def measure_qubits(alice_bits, alice_bases, num_qubits=None):
    """
    Bob measures all qubits from Alice in random bases.
    
    Args:
        alice_bits (list): Bits Alice prepared
        alice_bases (list): Bases Alice used
        num_qubits (int): Number of qubits to measure (defaults to length of alice_bits)
    
    Returns:
        tuple: (bob_bases, bob_results) - the bases Bob used and measurements
    """
    if num_qubits is None:
        num_qubits = len(alice_bits)
    
    bob_bases = [random_basis() for _ in range(num_qubits)]
    bob_results = []
    
    for i in range(num_qubits):
        measured_bit = measure_qubit(alice_bits[i], alice_bases[i], bob_bases[i])
        bob_results.append(measured_bit)
    
    return bob_bases, bob_results


def extract_key(alice_bits, alice_bases, bob_bases, bob_results):
    """
    Extract the shared key by keeping only bits where bases matched.
    
    Args:
        alice_bits (list): Bits Alice prepared
        alice_bases (list): Bases Alice used
        bob_bases (list): Bases Bob used
        bob_results (list): Bob's measurement results
    
    Returns:
        tuple: (shared_key, matching_indices)
    """
    shared_key = [alice_bits[i] for i in range(len(alice_bits)) if alice_bases[i] == bob_bases[i]]
    matching_indices = [i for i in range(len(alice_bits)) if alice_bases[i] == bob_bases[i]]
    return shared_key, matching_indices
