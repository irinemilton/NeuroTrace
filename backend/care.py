"""Role-scoped care workspace API for patient and caretaker experiences."""
from pathlib import Path
import sqlite3
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

DB_PATH = Path(__file__).resolve().parent / "care_workspace.sqlite3"
router = APIRouter(prefix="/api/care", tags=["care workspace"])


def connect() -> sqlite3.Connection:
    db = sqlite3.connect(DB_PATH)
    db.row_factory = sqlite3.Row
    return db


def initialise() -> None:
    with connect() as db:
        db.executescript("""
        CREATE TABLE IF NOT EXISTS routine_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT, time TEXT NOT NULL,
            icon TEXT NOT NULL, title TEXT NOT NULL, detail TEXT NOT NULL,
            completed INTEGER NOT NULL DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS game_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT, game TEXT NOT NULL,
            score INTEGER NOT NULL, total INTEGER NOT NULL,
            completed_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS medication_followups (
            id INTEGER PRIMARY KEY AUTOINCREMENT, time TEXT NOT NULL,
            title TEXT NOT NULL, detail TEXT NOT NULL, status TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS contacts (
            id INTEGER PRIMARY KEY AUTOINCREMENT, kind TEXT NOT NULL,
            name TEXT NOT NULL, detail TEXT NOT NULL, phone TEXT
        );
        """)
        if db.execute("SELECT COUNT(*) FROM routine_items").fetchone()[0] == 0:
            db.executemany("INSERT INTO routine_items(time,icon,title,detail,completed) VALUES (?,?,?,?,?)", [
                ("08:00", "💊", "Medication", "Take your morning medication", 0),
                ("09:00", "🍳", "Breakfast", "A calm, nourishing start", 0),
                ("10:00", "🧠", "Object Recall", "3 minute brain activity", 0),
                ("11:00", "🚶", "Gentle walk", "10 minutes of movement", 0),
                ("14:00", "🧩", "Pattern Match", "5 minute puzzle", 0),
                ("20:00", "💊", "Medication", "Evening medication reminder", 0),
            ])
        if db.execute("SELECT COUNT(*) FROM medication_followups").fetchone()[0] == 0:
            db.executemany("INSERT INTO medication_followups(time,title,detail,status) VALUES (?,?,?,?)", [
                ("08:00", "Morning medication", "Taken at 08:14", "done"),
                ("20:00", "Evening medication", "Reminder scheduled", "pending"),
            ])
        if db.execute("SELECT COUNT(*) FROM contacts").fetchone()[0] == 0:
            db.executemany("INSERT INTO contacts(kind,name,detail,phone) VALUES (?,?,?,?)", [
                ("doctor", "Dr. Elena Marquez", "Neurology care team", "+1 555 010 2040"),
                ("family", "Family contact", "Primary support contact", "+1 555 010 2041"),
            ])


initialise()


class GameResult(BaseModel):
    game: str = Field(min_length=1, max_length=80)
    score: int = Field(ge=0)
    total: int = Field(gt=0)


def rows(query: str) -> list[dict[str, Any]]:
    with connect() as db:
        return [dict(row) for row in db.execute(query).fetchall()]


@router.get("/patient")
def patient_workspace() -> dict[str, Any]:
    routine = rows("SELECT id,time,icon,title,detail,completed FROM routine_items ORDER BY time")
    results = rows("SELECT game,score,total,completed_at FROM game_results ORDER BY id DESC LIMIT 20")
    return {"role": "patient", "patient_name": "Margaret", "streak_days": 4,
            "routine": routine, "game_results": results,
            "weekly_summary": {"brain_activities": 5, "games": 8, "movement": 4, "routine_days": 6}}


@router.post("/patient/games", status_code=201)
def record_game(result: GameResult) -> dict[str, Any]:
    if result.score > result.total:
        raise HTTPException(status_code=422, detail="Score cannot exceed total.")
    with connect() as db:
        cursor = db.execute("INSERT INTO game_results(game,score,total) VALUES (?,?,?)", (result.game, result.score, result.total))
        return {"id": cursor.lastrowid, **result.model_dump()}


@router.post("/patient/routine/{item_id}/complete")
def complete_routine(item_id: int) -> dict[str, Any]:
    with connect() as db:
        cursor = db.execute("UPDATE routine_items SET completed=1 WHERE id=?", (item_id,))
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Routine item not found.")
    return {"id": item_id, "completed": True}


@router.get("/caretaker")
def caretaker_workspace() -> dict[str, Any]:
    return {"role": "caretaker", "patient_name": "Margaret",
            "medications": rows("SELECT id,time,title,detail,status FROM medication_followups ORDER BY time"),
            "contacts": rows("SELECT id,kind,name,detail,phone FROM contacts ORDER BY kind"),
            "safety": {"status": "clear", "message": "No new safety concerns reported."},
            "next_review": "Thursday, October 3 at 10:00 with Dr. Marquez"}


@router.post("/caretaker/medications/{medication_id}/follow-up")
def medication_followup(medication_id: int) -> dict[str, Any]:
    with connect() as db:
        cursor = db.execute("UPDATE medication_followups SET status='follow_up' WHERE id=?", (medication_id,))
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Medication not found.")
    return {"id": medication_id, "status": "follow_up"}
