class PreTrainedTokenizerBase:
    def encode(self, text: str) -> list[int]: ...


class AutoTokenizer:
    @staticmethod
    def from_pretrained(name: str) -> PreTrainedTokenizerBase: ...
