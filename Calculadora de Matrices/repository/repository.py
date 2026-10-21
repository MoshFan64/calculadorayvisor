import json
from pathlib import Path


class MatrixRepository:
    def __init__(self):
        self._storage_path = Path(__file__).parent.parent / "database" / "matrices.json"
        if self._storage_path.exists():
            matrices = json.loads(self._storage_path.read_text(encoding="utf-8"))
            if not isinstance(matrices, list) or any(
                not isinstance(matrix, dict) or not isinstance(matrix.get("id"), int)
                for matrix in matrices
            ):
                raise ValueError(f"Invalid matrix data in {self._storage_path}")
            self._data: dict[int, dict] = {matrix["id"]: matrix for matrix in matrices}
        else:
            self._data = {}
        self._next_id = max(self._data, default=0) + 1

    def _persist(self, matrices: dict[int, dict]) -> None:
        self._storage_path.parent.mkdir(parents=True, exist_ok=True)
        temporary_path = self._storage_path.with_suffix(".json.tmp")
        temporary_path.write_text(
            json.dumps(list(matrices.values()), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        temporary_path.replace(self._storage_path)

    def crear(self, matriz: dict) -> dict:
        matriz["id"] = self._next_id
        updated_data = {**self._data, self._next_id: matriz}
        self._persist(updated_data)
        self._data = updated_data
        self._next_id += 1
        return matriz

    def obtener(self, id: int) -> dict | None:
        return self._data.get(id)

    def listar(self) -> list[dict]:
        return list(self._data.values())

    def actualizar(self, id: int, matriz: dict) -> dict | None:
        if id not in self._data:
            return None
        matriz["id"] = id
        updated_data = {**self._data, id: matriz}
        self._persist(updated_data)
        self._data = updated_data
        return matriz

    def eliminar(self, id: int) -> dict | None:
        matriz = self._data.get(id)
        if matriz is None:
            return None
        updated_data = {key: value for key, value in self._data.items() if key != id}
        self._persist(updated_data)
        self._data = updated_data
        return matriz