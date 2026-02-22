from jinja2 import Environment, FileSystemLoader, select_autoescape
import os

template_dir = os.path.join(os.path.dirname(__file__), "..", "templates")
env = Environment(
    loader=FileSystemLoader(template_dir),
    autoescape=select_autoescape(["html"])
)


def _flatten(data: dict, prefix: str = "") -> list[dict]:
    """Recursively flatten nested dict into [{key, value}] rows."""
    rows = []
    for k, v in data.items():
        if k.startswith("_"):
            continue
        full_key = f"{prefix}.{k}" if prefix else k
        if isinstance(v, dict):
            rows.extend(_flatten(v, prefix=full_key))
        elif isinstance(v, list):
            for i, item in enumerate(v):
                if isinstance(item, dict):
                    rows.extend(_flatten(item, prefix=f"{full_key}[{i}]"))
                else:
                    rows.append({"key": f"{full_key}[{i}]", "value": str(item)})
        else:
            rows.append({"key": full_key, "value": str(v) if v is not None else "—"})
    return rows


def render_template(payload: dict, doc_id: str) -> str:
    template = env.get_template("email_generic.html")
    return template.render(
        title=payload.get("title") or payload.get("name") or payload.get("type") or "Submission",
        doc_id=doc_id,
        received_at=payload.get("_meta", {}).get("received_at", ""),
        rows=_flatten(payload),
    )
