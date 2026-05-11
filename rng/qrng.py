def random_basis():
	"""
	Randomly selects a quantum basis: 'Z' (computational) or 'X' (Hadamard) using quantum randomness.
	Returns: 'Z' or 'X'
	"""
	from qiskit import QuantumCircuit, execute
	from qiskit.providers.aer import Aer
	circuit = QuantumCircuit(1, 1)
	circuit.h(0)
	circuit.measure(0, 0)
	simulator = Aer.get_backend('qasm_simulator')
	result = execute(circuit, simulator, shots=1).result()
	bit = int(list(result.get_counts().keys())[0])
	return 'Z' if bit == 0 else 'X'

def qrng_bits(length):
	"""
	Generate a random binary string of given length, with random quantum basis for each bit.
	Args:
		length (int): Number of bits to generate.
	Returns:
		list of tuples: Each tuple is (bit, basis)
	"""
	from qiskit import QuantumCircuit, execute
	from qiskit.providers.aer import Aer

	bits = []
	simulator = Aer.get_backend('qasm_simulator')
	for _ in range(length):
		basis = random_basis()
		circuit = QuantumCircuit(1, 1)
		if basis == 'X':
			circuit.h(0)
		circuit.measure(0, 0)
		result = execute(circuit, simulator, shots=1).result()
		bit = int(list(result.get_counts().keys())[0])
		bits.append((bit, basis))
	return bits


def string_to_bits(s):
	return [int(b) for char in s.encode('utf-8') for b in format(char, '08b')]

def bits_to_string(bits):
	chars = []
	for b in range(0, len(bits), 8):
		byte = bits[b:b+8]
		if len(byte) < 8:
			break
		chars.append(chr(int(''.join(str(bit) for bit in byte), 2)))
	return ''.join(chars)

def xor_bits(data_bits, key_bits):
	key = (key_bits * ((len(data_bits) // len(key_bits)) + 1))[:len(data_bits)]
	return [d ^ k for d, k in zip(data_bits, key)]

def main():
	length = int(input("Enter number of random bits: "))
	bits = qrng_bits(length)
	print("Random bits with quantum bases:")
	for i, (bit, basis) in enumerate(bits):
		print(f"Bit {i+1}: {bit} (Basis: {basis})")

if __name__ == "__main__":
	main()
