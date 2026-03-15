from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from app.core.cancel import EventToken
from app.models.entities import Novel


@dataclass
class MLAvailability:
    available: bool
    error: str = ""


class MLProcessorAdapter:
    def __init__(self):
        self._train = None
        self._build_training_data = None
        self._prediction = None
        self._availability = self._load_dependencies()

    def _load_dependencies(self) -> MLAvailability:
        try:
            from ml_processor.train_model import train
            from ml_processor.labeler import build_training_data
            from ml_processor import prediction

            self._train = train
            self._build_training_data = build_training_data
            self._prediction = prediction
            return MLAvailability(available=True)
        except Exception as exc:
            return MLAvailability(
                available=False,
                error=(
                    "ml_processor is not available. Please install it before using ML cleanup flow\n"
                    f"Detail: {exc}"
                ),
            )

    @property
    def availability(self) -> MLAvailability:
        return self._availability

    def ensure_available(self) -> None:
        if not self._availability.available:
            raise RuntimeError(self._availability.error)

    def build_training_data(self) -> None:
        self.ensure_available()
        self._build_training_data()

    def train_model(self, cancel_token: EventToken) -> None:
        self.ensure_available()
        cancel_token.raise_if_cancelled()
        self._train()
        cancel_token.raise_if_cancelled()

    def load_model(self):
        self.ensure_available()
        return self._prediction.load_model()

    def predict_dataframe(self, model, tokenizer, text: str) -> pd.DataFrame:
        self.ensure_available()
        df = self._prediction.predict(model, tokenizer, text)
        if "Sentence" not in df.columns:
            raise ValueError("The prediction dataframe does not contain the 'Sentence' column.")
        if "Prediction" not in df.columns:
            raise ValueError("The prediction dataframe does not contain the 'Prediction' column.")
        if "Certainty" not in df.columns:
            df["Certainty"] = 0.0
        return df

    def run_predictions(self, novel: Novel, cancel_token: EventToken, progress_callback) -> Novel:
        cancel_token.raise_if_cancelled()
        model, tokenizer = self.load_model()
        total = len(novel.chapter_list)

        for idx, chapter in enumerate(novel.chapter_list, start=1):
            cancel_token.raise_if_cancelled()
            if progress_callback:
                progress_callback(idx, total, f"ML: {chapter.title}")
            if not chapter.content.strip():
                chapter.prediction_df = pd.DataFrame(columns=["Sentence", "Prediction", "Certainty"])
                continue

            df = self.predict_dataframe(model, tokenizer, chapter.content)
            chapter.prediction_df = df

        return novel

    def rebuild_chapter_content(self, novel: Novel, cancel_token: EventToken) -> Novel:
        for chapter in novel.chapter_list:
            cancel_token.raise_if_cancelled()
            df = chapter.prediction_df
            if df is None or df.empty:
                continue

            content = " ".join(df["Sentence"].tolist())
            # Remove extra spaces from joining sentences
            chapter.content = "\n".join(s.strip() for s in content.split('\n'))

        return novel
