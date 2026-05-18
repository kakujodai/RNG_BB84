from qiskit import QuantumCircuit
from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager #translator to IBM quantum computer language for H gate
from qiskit_ibm_runtime import QiskitRuntimeService, SamplerV2 as Sampler #logging into IBM computers online, sampler = "run this circuit lots of times and return measurement results"
import os
import sys


def make_rng_circuit(n: int):
    circuit = QuantumCircuit(n, n) #(qubits, classical bits) need classical bits to store measurements
    circuit.h(range(n)) #wont know if we're 0 or 1 until measured, true randomness babey
    circuit.measure(range(n), range(n))
    return circuit


def quantum_random_bits(num_bits: int, backend_name="ibm_kingston"):
    token = os.getenv("IBM_TOKEN") #cant put API key in public repo... im stoopid

    if token is None:
        raise ValueError("IBM_TOKEN is not set. Run: export IBM_TOKEN='your_token_here'")

    service = QiskitRuntimeService(
        channel="ibm_quantum_platform",
        token=token #api key
    )

    backend = service.backend(backend_name) #picked one of the available quantum computers on the site

    circuit = make_rng_circuit(num_bits) #call the function. argument = # of bits

    pm = generate_preset_pass_manager( #need this for hadamard
        backend=backend,
        optimization_level=1
    )

    isa_circuit = pm.run(circuit)

    sampler = Sampler(mode=backend) #tell the sampler to work with backend, sampler runs the circuit and collects measurements
    job = sampler.run([isa_circuit], shots=1) #one measurement = one random output

    print("Job submitted.")
    print("Job ID:", job.job_id()) #why not

    result = job.result()

    print("Status:", job.status())

    bitstrings = result[0].data.c.get_bitstrings() #measurement results stored here

    return bitstrings[0]


if __name__ == "__main__": #apparently detects if its run directly, if so use inline arguments

    if len(sys.argv) < 2:
        print("Usage: python3 RNG.py <num_bits>")
        sys.exit(1)

    num_bits = int(sys.argv[1]) #in line argument for # of bits to make

    bits = quantum_random_bits(num_bits)

    print(bits)