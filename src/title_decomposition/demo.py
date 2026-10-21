"""Optional Gradio interface; importing this module never loads a model."""
from __future__ import annotations

import argparse
import threading

from .inference import LocalParser
from .ranks import rank_record
from .schema import SchemaError

ADAPTERS = {
    "qing": "bruceyyu/qing-title-decomposition",
    "joseon": "bruceyyu/joseon-title-decomposition",
}
EXAMPLES = {
    "qing": [
        "頭品頂戴兵部侍郎兼都察院右副都御史巡撫貴州等處地方提督軍務兼理糧餉兼理各國事務大臣",
        "江西-瑞州府-高安縣-水利縣丞分駐南城",
        "甘肅-瑪喇巴什直隸廳-NA-花翎同知銜水利撫民通判",
        "欽命兵部左侍郎提督江西全省學政",
        "欽命翰林院編修提督湖南全省學政",
    ],
    "joseon": ["병조 판서", "승정원 승지"],
}


class DemoSession:
    """One lazily loaded model, with serialized inference to bound memory use."""

    def __init__(self, task: str, adapter: str, device_map: str = "auto"):
        if task not in ADAPTERS:
            raise ValueError(f"Unknown task: {task}")
        self.task, self.adapter, self.device_map = task, adapter, device_map
        self._model = None
        self._lock = threading.Lock()

    def decompose(self, title: str):
        if not isinstance(title, str) or not title.strip():
            return None, None, "Enter an official title."
        if len(title) > 1000:
            return None, None, "Enter one title of no more than 1,000 characters."
        try:
            with self._lock:
                if self._model is None:
                    self._model = LocalParser(self.adapter, task=self.task, device_map=self.device_map)
                record = self._model.parse(title)
                ranks = rank_record(record) if self.task == "qing" else None
        except SchemaError as exc:
            return None, None, f"Output rejected: {exc}"
        except Exception as exc:
            # Remote errors can contain signed URLs or authentication details.
            # Expose the exception type, never the raw remote exception.
            return None, None, (
                f"Inference failed ({type(exc).__name__}). Check model access, "
                "installed dependencies, network connectivity, and available memory."
            )
        return record, ranks, ""


def create_demo(task: str = "qing", adapter: str | None = None, device_map: str = "auto"):
    """Build a UI for one task; load weights only after a user requests inference."""
    try:
        import gradio as gr
    except ImportError as exc:
        raise RuntimeError("Install demo dependencies: pip install -e '.[inference,demo]'") from exc
    if task not in ADAPTERS:
        raise ValueError(f"Unknown task: {task}")
    adapter = adapter or ADAPTERS[task]
    session = DemoSession(task, adapter, device_map)

    def predict(title):
        record, ranks, error = session.decompose(title)
        if record is None:
            raise gr.Error(error)
        return record, ranks

    with gr.Blocks(title="Historical Official Title Decomposition", analytics_enabled=False) as app:
        gr.Markdown(
            "# Historical Official Title Decomposition\n"
            "Separate the institutional components of a bureaucratic title. "
            "For Qing titles, look up office, additional-title, and eligibility ranks separately.\n\n"
            f"**Task:** {task.capitalize()} · **Adapter:** `{adapter}` · "
            "[Paper](https://osf.io/preprints/socarxiv/eg87f_v1)"
        )
        title = gr.Textbox(label="Official title", lines=2, placeholder=EXAMPLES[task][0])
        gr.Examples([[text] for text in EXAMPLES[task]], inputs=title,
                    label="Illustrative titles", cache_examples=False)
        with gr.Row():
            run = gr.Button("Decompose title", variant="primary")
            clear = gr.ClearButton()
        with gr.Row():
            components = gr.JSON(label="Decomposed components", open=True)
            ranks = gr.JSON(label="Qing rank lookup", visible=task == "qing", open=True)
        if task == "qing":
            gr.Markdown(
                "**Reading the ranks:** 1a is more senior than 1b, through 9b. "
                "`unranked` is distinct from an absent or unmatched (`null`) value. "
                "A higher additional title does not imply a higher duty office."
            )
        run.click(predict, inputs=title, outputs=[components, ranks],
                  api_name="decompose", concurrency_limit=1)
        clear.add([title, components, ranks])
    return app.queue(max_size=8, default_concurrency_limit=1)


def main(argv: list[str] | None = None):
    parser = argparse.ArgumentParser(description="Local interactive official-title decomposition")
    parser.add_argument("--task", choices=tuple(ADAPTERS), default="qing")
    parser.add_argument("--adapter", help="Local PEFT adapter folder or Hugging Face repository ID")
    parser.add_argument("--device-map", default="auto", help="auto, cpu, mps, or cuda:0")
    parser.add_argument("--host", default="127.0.0.1", help="127.0.0.1 for local use; 0.0.0.0 only for intended hosting")
    parser.add_argument("--port", type=int, default=7860)
    args = parser.parse_args(argv)
    app = create_demo(args.task, args.adapter, args.device_map)
    app.launch(server_name=args.host, server_port=args.port, share=False,
               inbrowser=False, show_error=False, run_history=False,
               enable_monitoring=False, mcp_server=False)


if __name__ == "__main__":
    main()
