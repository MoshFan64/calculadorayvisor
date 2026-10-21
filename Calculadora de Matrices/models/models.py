from pydantic import BaseModel, field_validator

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