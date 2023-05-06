from __future__ import annotations

import warnings
from concurrent.futures import ThreadPoolExecutor
from itertools import repeat
from typing import Generator, Union

from .models.flair import Flair
from .models.torchmoji import TorchMoji
from .items import Sentiment, Output

InputType = Union[str, "list[str]"]


def divide_list(array: list, num: int) -> Generator[list, None, None]:
    """Divide a list into even chunks"""
    for i in range(0, len(array), num):
        yield array[i : i + num]

class Pipeline:
    """Efficient Wordsmyth text rating pipeline
    ```
    >>> from wordsmyth import Pipeline
    >>> Pipeline().eval("LOL").rating()
    0.5
    ```
    ```
    >>> from wordsmyth import Pipeline
    >>> [e.rating() for e in Pipeline().eval(["Not as great", "LOL"])]
    [0.1, 0.5]
    ```
    """
    def __init__(self) -> None:
        warnings.filterwarnings("ignore")
        self._flair = Flair()
        self._torchmoji = TorchMoji()

    def eval(
        self, text: Union[list[str], str], emojis: int = 10
    ) -> Union[Generator[Output, None, None], Output]:
        """Evaluate a text/list of text through both Flair and TorchMoji"""
        if isinstance(text, str):
            torchmoji = self._torchmoji.predict(text)
            flair = self._flair.predict(text)
            return Output(sentiment=Sentiment(**flair), emojis=torchmoji, text=text)

        text = list(divide_list(text, 5))
        with ThreadPoolExecutor(len(text)) as pool:
            flair = pool.map(self.flair, text)
            torchmoji = pool.map(self.torchmoji, text, repeat(emojis))
            for resf_, rest_, text_ in zip(flair, torchmoji, text):
                return (
                    Output(
                        sentiment=Sentiment(**fl_result),
                        emojis=tm_result,
                        text=input_text,
                    )
                    for fl_result, tm_result, input_text in zip(resf_, rest_, text_)
                )

    def flair(self, text: InputType) -> list[dict[str, Union[str, float]]]:
        """Evaluate a single text or a list of texts through Flair's `en-sentiment` model"""
        if isinstance(text, str):
            text = [text]
        return [self._flair.predict(sentence) for sentence in text]

    def torchmoji(self, text: InputType, top_n: int) -> list[list[str]]:
        """Evaluate a single text or a list of texts through the TorchMoji model"""
        if isinstance(text, str):
            text = [text]
        return [self._torchmoji.predict(sentence, top_n=top_n) for sentence in text]
