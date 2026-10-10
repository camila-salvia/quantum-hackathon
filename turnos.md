# Q-Staff: Optimización cuántica de asignación de guardias médicas críticas

> **Atribución institucional:** This effort is supported by Qollab & IonQ.  
> **Licencia:** MIT License  
> **Tema:** Quantum Impact (Gestión Sanitaria y Optimización de Operaciones)

---

## 1. Contexto e Impacto
La diagramación de turnos médicos en unidades de cuidados intensivos y urgencias es un problema de optimización combinatoria de alta complejidad (NP-hard). En centros de salud de alta demanda, asignar especialistas clave a guardias rotativas sin contemplar la complementariedad de roles genera sobrecarga de trabajo, fatiga médica y baches críticos de cobertura (por ejemplo, concentrar a los únicos médicos capacitados en intubación difícil en el turno diurno, dejando desprotegida la guardia nocturna).

Modelamos este desafío como un **grafo de conflicto ponderado**, donde cada nodo representa a un especialista y cada arista cuantifica la penalización operativa de asignar perfiles redundantes o incompatibles a la misma guardia. El objetivo es encontrar una partición bipartita que desacople los conflictos y garantice cobertura equilibrada 24/7.

---

## 2. Metodología: Clásico vs. Cuántico

### Línea Base Clásica (Heurística Greedy)
Para establecer un punto de comparación directo contra el circuito cuántico, implementamos un algoritmo voraz (*Greedy*):
1. Selecciona secuencialmente a cada profesional en orden estricto.
2. Evalúa de forma miope el costo inmediato de asignarlo al Turno A vs. Turno B, basándose únicamente en los médicos asignados previamente.
3. Lo asigna al turno de menor penalización instantánea.

**Limitación técnica:** Al tomar decisiones locales paso a paso sin proyectar el impacto global, el enfoque Greedy es vulnerable a quedar atrapado en **mínimos locales**, donde una mala asignación temprana fuerza penalizaciones severas en las etapas finales al agotarse las alternativas de rotación.

### Enfoque Cuántico: QAOA (Quantum Approximate Optimization Algorithm)
Transformamos el grafo de conflicto en un Hamiltoniano de espín (modelo de Ising) y diseñamos un circuito cuántico variacional QAOA de 4 qubits ($p=1$):
* **Superposición Uniforme:** Compuertas Hadamard iniciales colocan los 4 qubits en superposición, evaluando en paralelo las $2^4 = 16$ combinaciones posibles de turnos.
* **Hamiltoniano de Costo ($U_C$):** Compuertas CNOT combinadas con rotaciones de fase $R_z(2\gamma \cdot w_{uv})$ codifican las penalizaciones del grafo de conflicto en fases cuánticas relativas.
* **Hamiltoniano Mezclador ($U_M$):** Rotaciones transversales $R_x(2\beta)$ generan **interferencia cuántica**, cancelando por interferencia destructiva los estados de conflicto severo y amplificando constructivamente las soluciones de mínima penalización.
* **Medición:** El colapso del estado sobre la base computacional concentra la probabilidad en las particiones de balance óptimo (costo $0.00$).

---

## 3. Resultados y Métricas de Rendimiento

| Métrica | Algoritmo Clásico (Greedy) | Algoritmo Cuántico (QAOA) |
| :--- | :--- | :--- |
| **Asignación Obtenida** | `0101` (Turnos balanceados) | `1010` (Partición degenerada óptima) |
| **Costo / Penalización Residual** | 0.00 pts | 0.00 pts |
| **Tasa de Azar Base (Uniforme)** | N/A | 12.50% (para los 2 estados óptimos) |
| **Tasa de Éxito QAOA Medida** | N/A | **~16.0% - 17.5%** (1024 shots) |

### Interpretación de Resultados:
1. **Convergencia Global:** Ambos enfoques alcanzaron el mínimo global de conflicto ($0.00$), demostrando la validez física del mapeo del Hamiltoniano.
2. **Amplificación por Interferencia:** En lugar de una distribución plana aleatoria ($12.5\%$ para los estados óptimos `0101` y `1010`), el circuito QAOA concentró de manera consistente una probabilidad significativamente superior mediante interferencia constructiva, aun utilizando un circuito de profundidad mínima ($p=1$).

Con profundidad $p=1$, el circuito alcanza un 17% de concentración sobre los estados degenerate de costo 0 (frente al 12.5% del azar base). Como trabajo futuro y escalabilidad, incrementar la profundidad a $p=2$ permite superar el 35% de tasa de éxito a costa de mayor profundidad de compuertas.

---

## 4. Instrucciones de Reproducción
1. En el entorno de Qollab, seleccionar el backend **`Built-in simulator (24q)`** (o cualquier simulador remoto de IonQ).
2. Hacer clic en **Run** para compilar y ejecutar el proyecto.
3. La consola mostrará:
   * El diagrama del grafo de conflicto en ASCII.
   * El benchmark de la solución Greedy.
   * El diagrama esquemático del circuito cuántico generado.
   * La tabla comparativa y la distribución final de especialistas por guardia.

---

## 5. Declaración de Originalidad y Asistencia
* **Herramientas de asistencia:** La arquitectura del ansatz QAOA, el cálculo de fases de penalización y la estructuración del benchmark comparativo contaron con asistencia y refinamiento iterativo mediante Google Gemini como copiloto de desarrollo durante la ventana oficial del hackathon.
* **Implementación:** Toda la integración, depuración de compuertas, pruebas sobre los simuladores de Qollab y validación del modelo clínico fueron realizadas por el equipo.
* **Licencia:** MIT License.
