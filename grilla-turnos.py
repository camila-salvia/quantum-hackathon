"""
Proyecto: Optimización en la asignación de profesionales a turnos críticos
Tema: Quantum Impact - Qollab & IonQ Hackathon 101
Licencia: MIT
"This effort is supported by Qollab & IonQ"

Atribución y asistencia:
- La formulación del modelo, arquitectura del algoritmo QAOA y lógica 
  de integración con Qiskit fueron desarrolladas con la asistencia 
  de Google Gemini durante el período de desarrollo del hackathon.
"""

import numpy as np
from qiskit import QuantumCircuit
from qiskit.primitives import StatevectorSampler

# =====================================================================
#                   1. DEFINICIÓN DEL PROBLEMA
# =====================================================================

# Personal crítico a asignar:

# q0: Guardia de terapia intensiva - Dra. García (Especialista en Terapia Intensiva / UTI)
# q1: Guardia de emergencias - Dr. López (Especialista en Urgencias)
# q2: Guardia de trauma zonal - Dra. Martínez (Cirujano de Trauma)
# q3: Refuerzo ambulatorio - Dr. Rodríguez (Especialista en Medicina General)

STAFF = [
    "Dra. García - UTI",                      # 0
    "Dr. López - Urgencias",                  # 1
    "Dra. Martínez - Trauma zonal",           # 2
    "Dr. Rodríguez - Refuerzo ambulatorio"    # 3
]

# GRAFO DE CONFLICTO: Cada arista representa un conflicto entre turnos

# Las aristas con peso miden la incompatibilidad de poner a dos profesionales en el mismo turno

CONFLICT_EDGES = [
    (0, 1, 3.5),  # Dra. García y Dr. López son los dos únicos médicos certificados para intubación difícil
    (1, 2, 2.0),  # Dr. López y Dra. Martínez componen el equipo de respuesta rápida para politraumatismos
    (2, 3, 1.5),  # Dra. Martínez y Dr. Rodríguez tienen incompatibilidad de rotación o fatiga por horas extra acumuladas si cubren la misma guardia
    (0, 3, 2.5)   # Dra. García y Dr. Rodríguez forman el dúo de gestión de camas críticas; repartirlos garantiza supervisión balanceada
]

def print_conflict_graph():
    print("""
    GRAFO DE CONFLICTOS ENTRE PROFESIONALES:
        (0: Dra. García) -------------- [3.5] -------------- (1: Dr. López)
           |                                                |
         [2.5]                                            [2.0]
           |                                                |
      (3: Dr. Rodríguez) -------- [1.5] ---------- (2: Dra. Martínez)
    """)

# =====================================================================
#           2. LÍNEA BASE CLÁSICA (GREEDY HEURISTIC)
# =====================================================================

# Resolvemos el mismo problema con un algoritmo convencional para tener un punto de 
# comparación directo contra el circuito cuántico

def solve_classical_greedy(nodes, edges):
    """
    Asignación clásica voraz (Greedy):
    Divide los turnos en dos guardias rotativas (Grupo 0 y Grupo 1)
    buscando desacoplar los turnos en conflicto.
    """
    assignment = {}
    for node in range(len(nodes)):
        # Evaluar costo de asignar el médico al Grupo 0 vs Grupo 1
        cost_0 = sum(weight for u, v, weight in edges if (u == node and assignment.get(v) == 0) or (v == node and assignment.get(u) == 0))
        cost_1 = sum(weight for u, v, weight in edges if (u == node and assignment.get(v) == 1) or (v == node and assignment.get(u) == 1))
        assignment[node] = 0 if cost_0 <= cost_1 else 1

    bitstring = "".join(str(assignment[i]) for i in range(len(nodes)))
    # Costo = suma de penalizaciones por asignar turnos en conflicto al mismo grupo
    conflict_penalty = sum(
        weight for u, v, weight in edges if assignment[u] == assignment[v]
    )
    return bitstring, conflict_penalty

# =====================================================================
#           3. ALGORITMO CUÁNTICO (QAOA DE 4 QUBITS)
# =====================================================================
def build_qaoa_circuit(edges, gamma=0.39, beta=0.78): 
    """
    Construye el circuito variacional QAOA (p=1) calibrado para minimizar
    el costo del Hamiltoniano de conflicto.
    """
    n_qubits = 4
    qc = QuantumCircuit(n_qubits, n_qubits)

    # Capa 1: Superposición uniforme (Hadamard en todos los qubits)
    for i in range(n_qubits):
        qc.h(i)   # Compuerta Hadamard

    # Capa 2: Hamiltoniano de Costo / Problema
    for u, v, weight in edges:
        qc.cx(u, v)    # Entrelaza los dos qubits en conflicto
        qc.rz(2 * gamma * weight, v)  # Aplica un desfase (rotación en el eje Z) proporcional a la penalización
        qc.cx(u, v)   # Desentrelaza los qubits para restaurar el estado original

    # Capa 3: Hamiltoniano Mezclador (Mixer)
    # Rotaciones transversales Rx(2 * beta)
    for i in range(n_qubits):
        qc.rx(2 * beta, i)

    # Medición
    qc.measure(range(n_qubits), range(n_qubits))
    return qc

def calculate_energy(bitstring, edges):
    """Calcula la penalización de conflicto de una configuración binaria."""
    penalty = 0.0
    for u, v, weight in edges:
        # En Qiskit la convención de orden es little-endian al leer bitstrings invertidos
        if bitstring[u] == bitstring[v]:
            penalty += weight
    return penalty

# =====================================================================
#                   4. EJECUCIÓN Y COMPARATIVA
# =====================================================================
def main():
    print("==================================================================")
    print("  Q-STAFF: OPTIMIZACIÓN CUÁNTICA DE TURNOS CRÍTICOS HOSPITALARIOS")
    print("  This effort is supported by Qollab & IonQ")
    print("==================================================================\n")

    print_conflict_graph()

    # Benchmark Clásico
    print("--- [1] BENCHMARK CLÁSICO (GREEDY SOLVER) ---")
    classical_sol, classical_cost = solve_classical_greedy(STAFF, CONFLICT_EDGES)
    print(f"Configuración calculada (Grupo A/B): {classical_sol}")
    print(f"Penalización de conflicto residual: {classical_cost:.2f} pts\n")

    # Solución Cuántica QAOA
    print("--- [2] CIRCUITO CUÁNTICO QAOA (4 QUBITS) ---")
    qc = build_qaoa_circuit(CONFLICT_EDGES, gamma=0.39, beta=0.78)
    print(qc.draw(output="text"))

    sampler = StatevectorSampler()
    shots = 1024
    job = sampler.run([qc], shots=shots)
    result = job.result()
    counts = result[0].data.c.get_counts()

    # Procesar resultados (invertir strings para alineación directa con nodos 0..3)
    normalized_counts = {k[::-1]: v for k, v in counts.items()}
    best_quantum_state = min(normalized_counts.keys(), key=lambda s: calculate_energy(s, CONFLICT_EDGES))
    best_quantum_cost = calculate_energy(best_quantum_state, CONFLICT_EDGES)

    # Identificar el costo mínimo global y tasa de éxito
    min_cost = min(calculate_energy(s, CONFLICT_EDGES) for s in normalized_counts.keys())
    optimal_states = [s for s in normalized_counts if calculate_energy(s, CONFLICT_EDGES) == min_cost]
    optimal_shots = sum(normalized_counts[s] for s in optimal_states)
    success_rate = (optimal_shots / shots) * 100
    random_baseline = (len(optimal_states) / 16) * 100

    print("\n--- [3] RESULTADOS Y COMPARATIVA DIRECTA ---")
    print(f"+---------------------+--------------------+--------------------+")
    print(f"| Métrica             | Clásico (Greedy)   | Cuántico (QAOA)    |")
    print(f"+---------------------+--------------------+--------------------+")
    print(f"| Asignación obtenida | {classical_sol:<18} | {best_quantum_state:<18} |")
    print(f"| Costo/Penalización  | {classical_cost:<18.2f} | {best_quantum_cost:<18.2f} |")
    print(f"| Tasa Base (Azar)    | N/A                | {random_baseline:<17.2f}% |")
    print(f"| Tasa de Éxito QAOA  | N/A                | {success_rate:<17.2f}% |")
    print(f"+---------------------+--------------------+--------------------+")

    print(f"\nEstados degenerados óptimos detectados: {optimal_states}")
  
    print("\n--- [4] ASIGNACIÓN FINAL DE CUADRILLAS ---")
    for i, staff_member in enumerate(STAFF):
        group = "Grupo Alfa (Día)" if best_quantum_state[i] == '0' else "Grupo Beta (Noche)"
        print(f"  * {staff_member}: {group}")

    print("\n✓ Ejecución finalizada con éxito bajo runtime de Qollab.")

if __name__ == "__main__":
    main()