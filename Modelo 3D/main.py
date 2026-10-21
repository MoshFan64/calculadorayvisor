import csv
import math
from pathlib import Path
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import numpy as np
from fastapi.responses import HTMLResponse
 
app = FastAPI(title="3D Model & Matrix Transformation API")
 
# Habilitar CORS para permitir que Three.js se conecte sin restricciones
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
 
# Ruta al archivo CSV con las coordenadas (debe estar en el mismo directorio o volumen Docker)
CSV_FILE_PATH = Path("modelo_3d.csv")
 
 
def cargar_puntos_csv(path: Path) -> list[list[float]]:
    """Lee un archivo CSV con encabezados x,y,z y retorna una lista de vertices [[x, y, z], ...]."""
    puntos = []
    if not path.exists():
        print(f"Advertencia: No se encontró el archivo {path}")
        return puntos
 
    with open(path, mode="r", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        for row in reader:
            try:
                puntos.append([
                    float(row["x"]),
                    float(row["y"]),
                    float(row["z"])
                ])
            except (KeyError, ValueError) as e:
                # Omitir filas mal formadas o vacías
                continue
    return puntos
 
 
def create_transformation_matrix(tx: float, ty: float, tz: float, rx: float, ry: float, rz: float) -> list[float]:
    """Genera una matriz homogénea 4x4 (Traslación * Rotación Z-Y-X) en orden Column-Major para OpenGL/Three.js."""
    rad_x, rad_y, rad_z = math.radians(rx), math.radians(ry), math.radians(rz)
 
    # Matriz de Rotación X
    Rx = np.array([
        [1, 0, 0, 0],
        [0, np.cos(rad_x), -np.sin(rad_x), 0],
        [0, np.sin(rad_x), np.cos(rad_x), 0],
        [0, 0, 0, 1]
    ])
 
    # Matriz de Rotación Y
    Ry = np.array([
        [np.cos(rad_y), 0, np.sin(rad_y), 0],
        [0, 1, 0, 0],
        [-np.sin(rad_y), 0, np.cos(rad_y), 0],
        [0, 0, 0, 1]
    ])
 
    # Matriz de Rotación Z
    Rz = np.array([
        [np.cos(rad_z), -np.sin(rad_z), 0, 0],
        [np.sin(rad_z), np.cos(rad_z), 0, 0],
        [0, 0, 1, 0],
        [0, 0, 0, 1]
    ])
 
    # Matriz de Traslación
    T = np.array([
        [1, 0, 0, tx],
        [0, 1, 0, ty],
        [0, 0, 1, tz],
        [0, 0, 0, 1]
    ])
 
    # Transformación compuesta: M = T @ Rz @ Ry @ Rx
    M = T @ Rz @ Ry @ Rx
 
    # Transponer (.T) a Column-Major order y aplanar a lista de 16 floats
    return M.T.flatten().tolist()
 
 
@app.get("/")
def read_root():
    """Endpoint raíz para verificar disponibilidad del servicio."""
    return {
        "status": "online",
        "message": "API de Modelo 3D y Transformaciones Matriciales activa",
        "endpoints": {
            "csv_model": "/api/modelo-csv",
            "websocket": "/ws/transform",
            "docs": "/docs"
        }
    }
 
 
@app.get("/api/modelo-csv")
def obtener_puntos_modelo():
    """Devuelve los vértices 3D parseados desde el archivo CSV."""
    puntos = cargar_puntos_csv(CSV_FILE_PATH)
    return {
        "total_puntos": len(puntos),
        "vertices": puntos
    }
 
 
@app.websocket("/ws/transform")
async def websocket_transform(websocket: WebSocket):
    """Canal WebSocket para recibir parámetros de movimiento y enviar matrices 4x4."""
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_json()
 
            # Extraer traslaciones y rotaciones recibidas
            t_x = float(data.get("tx", 0.0))
            t_y = float(data.get("ty", 0.0))
            t_z = float(data.get("tz", 0.0))
            r_x = float(data.get("rx", 0.0))
            r_y = float(data.get("ry", 0.0))
            r_z = float(data.get("rz", 0.0))
 
            # Calcular la matriz 4x4
            matrix_4x4 = create_transformation_matrix(t_x, t_y, t_z, r_x, r_y, r_z)
 
            # Responder con la matriz procesada
            await websocket.send_json({
                "matrix": matrix_4x4,
                "status": "ok"
            })
    except WebSocketDisconnect:
        print("Cliente WebSocket desconectado")
 
@app.get("/view", response_class=HTMLResponse)
def serve_viewer():
    """Servidor web directo para ver la interfaz 3D."""
    with open("index.html", "r", encoding="utf-8") as f:
        return f.read()