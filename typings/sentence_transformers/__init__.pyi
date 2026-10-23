import numpy as np
from numpy.typing import NDArray


class CrossEncoder:
    def __init__(self, model_name_or_path: str, device: str) -> None: ...
    def predict(
        self,
        sentences: list[tuple[str, str]],
        *,
        batch_size: int,
    ) -> NDArray[np.float32]: ...


class SentenceTransformer:
    def __init__(self, model_name_or_path: str, device: str) -> None: ...
    def encode(
        self,
        sentences: list[str],
        batch_size: int,
        normalize_embeddings: bool,
        convert_to_numpy: bool,
    ) -> NDArray[np.float32]: ...
