from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from pathlib import Path
import threading
import json

app = FastAPI(title="Groceries List")

DATA_FILE = Path(__file__).parent / "data" / "groceries.json"
STORES = ["indian", "costco", "wholefoods", "farmersmarket"]

_lock = threading.Lock()


# ── JSON helpers ──────────────────────────────────────────────────────────────

def read_data() -> dict:
    if not DATA_FILE.exists():
        data = {store: [] for store in STORES}
        write_data(data)
        return data
    with open(DATA_FILE) as f:
        data = json.load(f)
    # ensure all stores present even if file was hand-edited
    for store in STORES:
        data.setdefault(store, [])
    return data


def write_data(data: dict) -> None:
    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")


# ── Routes ────────────────────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
def index():
    html_path = Path(__file__).parent / "static" / "index.html"
    return html_path.read_text()


@app.get("/api/items/{store}")
def get_items(store: str):
    if store not in STORES:
        raise HTTPException(status_code=404, detail="Unknown store")
    with _lock:
        data = read_data()
    return [{"index": i, "name": name} for i, name in enumerate(data[store])]


class ItemIn(BaseModel):
    name: str


@app.post("/api/items/{store}", status_code=201)
def add_item(store: str, item: ItemIn):
    if store not in STORES:
        raise HTTPException(status_code=404, detail="Unknown store")
    name = item.name.strip()
    if not name:
        raise HTTPException(status_code=400, detail="Item name cannot be empty")
    with _lock:
        data = read_data()
        data[store].append(name)
        write_data(data)
    return {"index": len(data[store]) - 1, "name": name}


@app.delete("/api/items/{store}/all")
def clear_store(store: str):
    if store not in STORES:
        raise HTTPException(status_code=404, detail="Unknown store")
    with _lock:
        data = read_data()
        data[store] = []
        write_data(data)
    return {"ok": True}


@app.delete("/api/items/{store}/{index}")
def delete_item(store: str, index: int):
    if store not in STORES:
        raise HTTPException(status_code=404, detail="Unknown store")
    with _lock:
        data = read_data()
        if index < 0 or index >= len(data[store]):
            raise HTTPException(status_code=404, detail="Item not found")
        data[store].pop(index)
        write_data(data)
    return {"ok": True}
