def sumar(m1: list[list[float]], m2: list[list[float]]) -> list[list[float]]:
    if len(m1) != len(m2) or len(m1[0]) != len(m2[0]):
        raise ValueError("las matrices deben tener la misma dimensión")
    return [[a + b for a, b in zip(fila1, fila2)] for fila1, fila2 in zip(m1, m2)]

def transponer(m: list[list[float]]) -> list[list[float]]:
    return [list(fila) for fila in zip(*m)]

def multiplicar(m1: list[list[float]], m2: list[list[float]]) -> list[list[float]]:
    if not m1 or not m2 or len(m1[0]) != len(m2):
        raise ValueError("el número de columnas de la primera matriz debe coincidir con las filas de la segunda")
    return [
        [sum(fila[k] * m2[k][columna] for k in range(len(m2))) for columna in range(len(m2[0]))]
        for fila in m1
    ]

def determinante(m: list[list[float]]) -> float:
    if not m or any(len(fila) != len(m) for fila in m):
        raise ValueError("la matriz debe ser cuadrada")

    matriz = [fila[:] for fila in m]
    resultado = 1.0
    for columna in range(len(matriz)):
        pivote = max(range(columna, len(matriz)), key=lambda fila: abs(matriz[fila][columna]))
        if matriz[pivote][columna] == 0:
            return 0.0
        if pivote != columna:
            matriz[columna], matriz[pivote] = matriz[pivote], matriz[columna]
            resultado *= -1
        pivote_valor = matriz[columna][columna]
        resultado *= pivote_valor
        for fila in range(columna + 1, len(matriz)):
            factor = matriz[fila][columna] / pivote_valor
            for indice in range(columna + 1, len(matriz)):
                matriz[fila][indice] -= factor * matriz[columna][indice]
    return resultado