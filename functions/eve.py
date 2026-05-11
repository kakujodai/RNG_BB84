"""
Eve's different eavesdropping attack strategies in the BB84 protocol.
Eve attempts to intercept and measure Alice's qubits before they reach Bob.
"""

from rng.qrng import random_basis
from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator


def measure_qubit(qubit_bit, qubit_basis, measure_basis):
    """
    Measure a single qubit using Qiskit simulator.
    
    Args:
        qubit_bit (int): The bit value (0 or 1)
        qubit_basis (str): The basis the qubit is in ('Z' or 'X')
        measure_basis (str): The basis to measure in ('Z' or 'X')
    
    Returns:
        int: The measured bit (0 or 1)
    """
    simulator = AerSimulator()
    qc = QuantumCircuit(1, 1)
    
    # Encode bit first, then rotate basis.
    # For X-basis, bit=1 must become |->, which is H(X|0>).
    if qubit_bit == 1:
        qc.x(0)
    if qubit_basis == 'X':
        qc.h(0)
    
    # Measure in the specified basis
    if measure_basis == 'X':
        qc.h(0)
    
    qc.measure(0, 0)
    compiled = transpile(qc, simulator)
    result = simulator.run(compiled, shots=1).result()
    measured_bit = int(list(result.get_counts().keys())[0])
    return measured_bit


class EveAttack:
    """Base class for Eve's attack strategies."""
    
    def __init__(self, name):
        self.name = name
        self.eve_bases = []
        self.eve_results = []
    
    def attack(self, alice_bits, alice_bases):
        """
        Perform the attack.
        
        Args:
            alice_bits (list): Bits Alice prepared
            alice_bases (list): Bases Alice used
        
        Returns:
            list: The bits Eve forward to Bob (may be modified by the attack)
        """
        raise NotImplementedError("Subclasses must implement attack()")
    
    def get_stats(self):
        """Return statistics about the attack."""
        return {
            'name': self.name,
            'num_measurements': len(self.eve_results),
            'eve_bases': self.eve_bases,
            'eve_results': self.eve_results
        }


class MeasureAndResendAttack(EveAttack):
    """
    Measure-and-Resend Attack: Eve measures in random bases and forwards her measurement results.
    This is the most basic attack and causes detectable errors when Eve uses wrong basis.
    """
    
    def __init__(self):
        super().__init__("Measure-and-Resend")
    
    def attack(self, alice_bits, alice_bases):
        """
        Eve measures each qubit in a random basis and forwards her measurement to Bob.
        
        Args:
            alice_bits (list): Bits Alice prepared
            alice_bases (list): Bases Alice used
        
        Returns:
            tuple: (eve_bases, eve_results, forwarded_bits)
        """
        self.eve_bases = [random_basis() for _ in range(len(alice_bits))]
        self.eve_results = []
        forwarded_bits = []
        
        for i in range(len(alice_bits)):
            # Eve measures the qubit
            measured_bit = measure_qubit(alice_bits[i], alice_bases[i], self.eve_bases[i])
            self.eve_results.append(measured_bit)
            forwarded_bits.append(measured_bit)
        
        return self.eve_bases, self.eve_results, forwarded_bits


class InterceptAndReplaceAttack(EveAttack):
    """
    Intercept-and-Replace Attack: Eve measures and immediately reconstructs what she thinks
    the qubit should be based on her measurement. This introduces errors when she measured wrong.
    """
    
    def __init__(self):
        super().__init__("Intercept-and-Replace")
    
    def attack(self, alice_bits, alice_bases):
        """
        Eve measures and attempts to recreate the qubit state.
        
        Args:
            alice_bits (list): Bits Alice prepared
            alice_bases (list): Bases Alice used
        
        Returns:
            tuple: (eve_bases, eve_results, reconstructed_bits)
        """
        self.eve_bases = [random_basis() for _ in range(len(alice_bits))]
        self.eve_results = []
        reconstructed_bits = []
        
        for i in range(len(alice_bits)):
            # Eve measures the qubit
            measured_bit = measure_qubit(alice_bits[i], alice_bases[i], self.eve_bases[i])
            self.eve_results.append(measured_bit)
            # She forwards her measured bit (same as measure-and-resend in terms of forwarded value)
            reconstructed_bits.append(measured_bit)
        
        return self.eve_bases, self.eve_results, reconstructed_bits


class ClonedStateAttack(EveAttack):
    """
    Cloned State Attack: Eve attempts to clone the quantum state (theoretically impossible,
    but we simulate limited eavesdropping capability).
    """
    
    def __init__(self):
        super().__init__("Cloned-State")
    
    def attack(self, alice_bits, alice_bases):
        """
        Eve tries to measure without significantly disturbing the qubit.
        In practice, she still measures in random bases (quantum no-cloning prevents true cloning).
        
        Args:
            alice_bits (list): Bits Alice prepared
            alice_bases (list): Bases Alice used
        
        Returns:
            tuple: (eve_bases, eve_results, forwarded_bits)
        """
        # In reality, this is same as measure-and-resend since you can't clone quantum states
        self.eve_bases = [random_basis() for _ in range(len(alice_bits))]
        self.eve_results = []
        forwarded_bits = []
        
        for i in range(len(alice_bits)):
            measured_bit = measure_qubit(alice_bits[i], alice_bases[i], self.eve_bases[i])
            self.eve_results.append(measured_bit)
            forwarded_bits.append(measured_bit)
        
        return self.eve_bases, self.eve_results, forwarded_bits


class NoAttack(EveAttack):
    """No attack - Eve is not present or not attacking."""
    
    def __init__(self):
        super().__init__("No-Attack")
    
    def attack(self, alice_bits, alice_bases):
        """
        No attack occurs - bits pass through unchanged.
        
        Args:
            alice_bits (list): Bits Alice prepared
            alice_bases (list): Bases Alice used
        
        Returns:
            tuple: (eve_bases, eve_results, forwarded_bits)
        """
        self.eve_bases = []
        self.eve_results = []
        return [], [], alice_bits


def create_attack(attack_type="measure-and-resend"):
    """
    Factory function to create different Eve attack objects.
    
    Args:
        attack_type (str): Type of attack ('measure-and-resend', 'intercept-and-replace', 'cloned-state', 'none')
    
    Returns:
        EveAttack: Attack object instance
    """
    attacks = {
        'measure-and-resend': MeasureAndResendAttack,
        'intercept-and-replace': InterceptAndReplaceAttack,
        'cloned-state': ClonedStateAttack,
        'none': NoAttack
    }
    
    attack_class = attacks.get(attack_type.lower(), MeasureAndResendAttack)
    return attack_class()
