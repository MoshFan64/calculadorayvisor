# main.py
import csv
import math
from pathlib import Path

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
import uvicorn
from models.models import MatrixCreate
from repository.repository import MatrixRepository
import services.services as services

app = FastAPI()
repo = MatrixRepository()
CSV_FILE_PATH = Path(__file__).parent / "data" / "modelo_3d.csv"

@app.get("/")
def servir_frontend():
    return FileResponse(Path(__file__).parent / "web" / "index.html")

@app.get("/view")
def serve_viewer():
    return FileResponse(Path(__file__).parent / "web" / "visualizador.html")

@app.get("/api/renderizador")
def estado_renderizador():
    return {
        "status": "online",
        "message": "API de Calculadora de Matrices y Renderizador 3D activa",
        "endpoints": {
            "csv_model": "/api/modelo-csv",
            "websocket": "/ws/transform",
            "viewer": "/view",
            "docs": "/docs",
        },
    }

@app.get("/api/modelo-csv")
def obtener_puntos_modelo():
    if not CSV_FILE_PATH.is_file():
        raise HTTPException(500, "No se encontró el archivo de puntos del modelo 3D")

    vertices = []
    with CSV_FILE_PATH.open(mode="r", encoding="utf-8", newline="") as file:
        reader = csv.DictReader(file)
        if not {"x", "y", "z"}.issubset(reader.fieldnames or []):
            raise HTTPException(500, "El CSV del modelo debe incluir las columnas x, y, z")
        for line_number, row in enumerate(reader, start=2):
            try:
                vertices.append([float(row["x"]), float(row["y"]), float(row["z"])])
            except (TypeError, ValueError) as error:
                raise HTTPException(500, f"Fila {line_number} inválida en el CSV del modelo") from error

    return {"total_puntos": len(vertices), "vertices": vertices}

def create_transformation_matrix(tx: float, ty: float, tz: float, rx: float, ry: float, rz: float) -> list[float]:
    rad_x, rad_y, rad_z = math.radians(rx), math.radians(ry), math.radians(rz)
    cos_x, sin_x = math.cos(rad_x), math.sin(rad_x)
    cos_y, sin_y = math.cos(rad_y), math.sin(rad_y)
    cos_z, sin_z = math.cos(rad_z), math.sin(rad_z)

    rotation_x = [
        [1, 0, 0, 0],
        [0, cos_x, -sin_x, 0],
        [0, sin_x, cos_x, 0],
        [0, 0, 0, 1],
    ]
    rotation_y = [
        [cos_y, 0, sin_y, 0],
        [0, 1, 0, 0],
        [-sin_y, 0, cos_y, 0],
        [0, 0, 0, 1],
    ]
    rotation_z = [
        [cos_z, -sin_z, 0, 0],
        [sin_z, cos_z, 0, 0],
        [0, 0, 1, 0],
        [0, 0, 0, 1],
    ]
    translation = [
        [1, 0, 0, tx],
        [0, 1, 0, ty],
        [0, 0, 1, tz],
        [0, 0, 0, 1],
    ]

    def multiply(left: list[list[float]], right: list[list[float]]) -> list[list[float]]:
        return [
            [sum(left[row][index] * right[index][column] for index in range(4)) for column in range(4)]
            for row in range(4)
        ]

    matrix = multiply(translation, multiply(rotation_z, multiply(rotation_y, rotation_x)))
    return [matrix[row][column] for column in range(4) for row in range(4)]

def compose_transformation_matrices(transformation: list[float], base: list[float]) -> list[float]:
    transformation_rows = [
        [transformation[column * 4 + row] for column in range(4)]
        for row in range(4)
    ]
    base_rows = [
        [base[column * 4 + row] for column in range(4)]
        for row in range(4)
    ]
    composed = [
        [
            sum(transformation_rows[row][index] * base_rows[index][column] for index in range(4))
            for column in range(4)
        ]
        for row in range(4)
    ]
    return [composed[row][column] for column in range(4) for row in range(4)]

@app.websocket("/ws/transform")
async def websocket_transform(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_json()
            if not isinstance(data, dict):
                await websocket.send_json({"status": "error", "detail": "Se esperaba un objeto JSON"})
                continue

            try:
                parameters = {
                    name: float(data.get(name, 0.0))
                    for name in ("tx", "ty", "tz", "rx", "ry", "rz")
                }
                if not all(math.isfinite(value) for value in parameters.values()):
                    raise ValueError("Los parámetros deben ser números finitos")
                base_matrix = data.get("base_matrix")
                if base_matrix is not None:
                    if not isinstance(base_matrix, list) or len(base_matrix) != 16:
                        raise ValueError("La matriz base debe contener 16 valores")
                    base_matrix = [float(value) for value in base_matrix]
                    if not all(math.isfinite(value) for value in base_matrix):
                        raise ValueError("Los valores de la matriz base deben ser finitos")
            except (TypeError, ValueError) as error:
                await websocket.send_json({
                    "status": "error",
                    "detail": str(error),
                    "request_id": data.get("request_id"),
                    "generation": data.get("generation"),
                })
                continue

            matrix = create_transformation_matrix(**parameters)
            if base_matrix is not None:
                matrix = compose_transformation_matrices(matrix, base_matrix)
            await websocket.send_json({
                "matrix": matrix,
                "status": "ok",
                "request_id": data.get("request_id"),
                "generation": data.get("generation"),
            })
    except WebSocketDisconnect:
        pass

@app.post("/matrices")
def crear_matriz(payload: MatrixCreate):
    return repo.crear(payload.model_dump())

@app.get("/matrices")
def listar_matrices():
    return repo.listar()

@app.get("/matrices/{id}")
def obtener_matriz(id: int):
    matriz = repo.obtener(id)
    if not matriz:
        raise HTTPException(404, "matriz no encontrada")
    return matriz

@app.put("/matrices/{id}")
def actualizar_matriz(id: int, payload: MatrixCreate):
    matriz = repo.actualizar(id, payload.model_dump())
    if not matriz:
        raise HTTPException(404, "matriz no encontrada")
    return matriz

@app.delete("/matrices/{id}")
def eliminar_matriz(id: int):
    matriz = repo.eliminar(id)
    if not matriz:
        raise HTTPException(404, "matriz no encontrada")
    return {"mensaje": "matriz eliminada", "id": id}

@app.post("/operaciones/sumar")
def sumar_matrices(id1: int, id2: int):
    m1, m2 = repo.obtener(id1), repo.obtener(id2)
    if not m1 or not m2:
        raise HTTPException(404, "matriz no encontrada")
    try:
        return {"resultado": services.sumar(m1["datos"], m2["datos"])}
    except ValueError as e:
        raise HTTPException(400, str(e))

@app.post("/operaciones/multiplicar")
def multiplicar_matrices(id1: int, id2: int):
    m1, m2 = repo.obtener(id1), repo.obtener(id2)
    if not m1 or not m2:
        raise HTTPException(404, "matriz no encontrada")
    try:
        return {"resultado": services.multiplicar(m1["datos"], m2["datos"])}
    except ValueError as e:
        raise HTTPException(400, str(e))

@app.get("/matrices/{id}/transpuesta")
def transpuesta_matriz(id: int):
    matriz = repo.obtener(id)
    if not matriz:
        raise HTTPException(404, "matriz no encontrada")
    return {"resultado": services.transponer(matriz["datos"])}

@app.get("/matrices/{id}/determinante")
def determinante_matriz(id: int):
    matriz = repo.obtener(id)
    if not matriz:
        raise HTTPException(404, "matriz no encontrada")
    try:
        return {"resultado": services.determinante(matriz["datos"])}
    except ValueError as e:
        raise HTTPException(400, str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)