"""Inference is opt-in. Importing this module never downloads or queries a model."""
from __future__ import annotations
import json
from pathlib import Path

from ._qing_protocol import extract_json_object
from .prompts import user_message
from .schema import validate_record

BASE_MODEL = "Qwen/Qwen3.5-4B"


def _check_adapter_task(adapter: str, task: str) -> None:
    path = Path(adapter) / "inference_config.json"
    if Path(adapter).is_dir():
        metadata = json.loads(path.read_text()) if path.is_file() else {}
        if metadata.get("task", task) != task:
            raise ValueError("The adapter belongs to a different task")
        if metadata.get("prompt_version", "current") != "current":
            raise ValueError("This adapter uses an unsupported instruction version")
        return
    from huggingface_hub import hf_hub_download
    from huggingface_hub.errors import EntryNotFoundError
    try:
        path = Path(hf_hub_download(adapter, "inference_config.json"))
    except EntryNotFoundError:
        return
    metadata = json.loads(path.read_text())
    if metadata.get("task", task) != task:
        raise ValueError("The adapter belongs to a different task")
    if metadata.get("prompt_version", "current") != "current":
        raise ValueError("This adapter uses an unsupported instruction version")


class LocalParser:
    """Load a base model plus an exported PEFT adapter on explicitly requested use."""

    def __init__(self, adapter: str, task: str = "qing", base_model: str = BASE_MODEL,
                 device_map: str = "auto", max_tokens: int | None = None):
        if task not in ("qing", "joseon"):
            raise ValueError(f"Unknown task: {task}")
        try:
            from transformers import AutoModelForImageTextToText, AutoTokenizer
            from peft import PeftConfig, PeftModel
        except ImportError as exc:
            raise RuntimeError('Install the optional inference dependencies: pip install ".[inference]"') from exc
        self.task = task
        _check_adapter_task(adapter, task)
        self.max_tokens = max_tokens or (512 if task == "qing" else 256)
        config = PeftConfig.from_pretrained(adapter)
        if config.base_model_name_or_path != base_model:
            raise ValueError("The requested base model differs from the adapter configuration")
        self.tokenizer = AutoTokenizer.from_pretrained(base_model, revision=config.revision)
        base = AutoModelForImageTextToText.from_pretrained(
            base_model, revision=config.revision, device_map=device_map, dtype="auto")
        self.model = PeftModel.from_pretrained(base, adapter)
        self.model.eval()

    def parse(self, title: str) -> dict:
        import torch
        text = self.tokenizer.apply_chat_template(
            [user_message(title, self.task)], tokenize=False,
            add_generation_prompt=True, enable_thinking=False)
        inputs = self.tokenizer(text, return_tensors="pt").to(self.model.device)
        with torch.inference_mode():
            output = self.model.generate(**inputs, do_sample=False, max_new_tokens=self.max_tokens,
                                         pad_token_id=self.tokenizer.eos_token_id)
        raw = self.tokenizer.decode(output[0, inputs["input_ids"].shape[-1]:], skip_special_tokens=True)
        return validate_record(extract_json_object(raw), self.task, title)



