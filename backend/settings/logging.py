# utils/logging.py  (new file)
import logging, os, time
from urllib.parse import urlencode

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        fmt = "%(asctime)s %(levelname)s [%(name)s] %(message)s"
        handler.setFormatter(logging.Formatter(fmt))
        logger.addHandler(handler)
    logger.setLevel(getattr(logging, LOG_LEVEL, logging.INFO))
    return logger

def mask_api_key(v: str | None) -> str:
    if not v: return ""
    return f"{v[:4]}...{v[-4:]}"

class Timer:
    def __enter__(self):
        self.t0 = time.perf_counter(); return self
    def __exit__(self, *exc):
        self.ms = int((time.perf_counter() - self.t0) * 1000)

def safe_query(params: dict) -> str:
    # don’t ever log raw api_key
    p = dict(params)
    if "api_key" in p:
        p["api_key"] = mask_api_key(str(p["api_key"]))
    return urlencode(p, doseq=True)
