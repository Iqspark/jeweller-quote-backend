from jinja2 import Environment, FileSystemLoader, select_autoescape
import os
import logging

logger = logging.getLogger(__name__)

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


def _is_jeweller_quote(payload: dict) -> bool:
    """Detect if payload is a jeweller insurance quote."""
    jeweller_keys = {"firm_name", "cadLimit", "rates", "adjustments", "insurance_start_date"}
    return jeweller_keys.issubset(payload.keys())


def render_template(payload: dict, doc_id: str) -> str:
    logger.info(f"Keys in payload: {list(payload.keys())[:5]}")
    logger.info(f"Is jeweller quote: {_is_jeweller_quote(payload)}")

    # List available templates
    available = os.listdir(template_dir)
    logger.debug(f"Available templates: {available}")

    #Choose and render the correct template based on payload shape.
    if _is_jeweller_quote(payload):
        logger.info(f"Using jeweller quote template for doc {doc_id}")
        try:
            template = env.get_template("email_jeweller_quote.html")
            return template.render(data=payload, doc_id=doc_id)
        except Exception as e:
            logger.error(f"Jeweller template render failed: {e}")
            raise
    # Fallback: generic template for any other JSON
    # Fallback: generic template for any other JSON
    logger.info(f"Using generic template for doc {doc_id}")
    try:
        template = env.get_template("email_generic.html")
        return template.render(
            title=payload.get("title") or payload.get("name") or payload.get("type") or "Submission",
            doc_id=doc_id,
            received_at=payload.get("_meta", {}).get("received_at", ""),
            rows=_flatten(payload),
        )
    except Exception as e:
        logger.error(f"Generic template render failed: {e}")
        raise