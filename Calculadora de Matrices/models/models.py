from typing import Annotated

from pydantic import BaseModel, Field, field_validator

FloatFinito = Annotated[float, Field(allow_inf_nan=False)]

class MatrixCreate(BaseModel):
    nombre: str
    datos: list[list[float]]


    @field_validator("datos")
    @classmethod
    def filas_parejas(cls, v):
        largos = [len(fila) for fila in v]
        if len(set(largos)) > 1:
            raise ValueError("Todas las filas deben tener el mismo largo")
        return v;

class MatrixOut(MatrixCreate):
    id: int

class TransformRequest(BaseModel):
    tx: FloatFinito = 0.0
    ty: FloatFinito = 0.0
    tz: FloatFinito = 0.0
    rx: FloatFinito = 0.0
    ry: FloatFinito = 0.0
    rz: FloatFinito = 0.0
    base_matrix: list[FloatFinito] | None = Field(default=None, min_length=16, max_length=16)