import json
from datetime import date
from typing import Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from database import get_connection, init_db

app = FastAPI(title="SoftSoul Infra E-Quoter API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ItemIn(BaseModel):
    name: str
    custom_name: str = ''
    qty: float = 1
    length: float = 0
    width: float = 0
    rate: float = 0


class RoomIn(BaseModel):
    type: str
    name: str
    sort_order: int = 0
    items: list[ItemIn] = []


class ProjectIn(BaseModel):
    code: str
    client_name: str = ''
    client_phone: str = ''
    client_email: str = ''
    client_address: str = ''
    client_site: str = ''
    project_type: str = ''
    project_date: str = ''
    project_timeline: str = ''
    discount: float = 0
    gst: float = 0
    notes: str = ''
    company_name: str = 'SoftSoul Infra'
    company_addr: str = ''
    company_phone: str = ''
    company_email: str = ''
    company_web: str = ''
    rooms: list[RoomIn] = []


class ProjectOut(BaseModel):
    id: int
    code: str
    created_at: str
    updated_at: str
    client_name: str
    client_phone: str
    client_email: str
    client_address: str
    client_site: str
    project_type: str
    project_date: str
    project_timeline: str
    discount: float
    gst: float
    notes: str
    company_name: str
    company_addr: str
    company_phone: str
    company_email: str
    company_web: str
    rooms: list[dict] = []


@app.on_event("startup")
def startup():
    try:
        init_db()
        print("Database tables ready")
    except Exception as e:
        print(f"DB init skipped (run schema.sql manually if needed): {e}")


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.post("/api/quotes", status_code=201)
def save_quote(proj: ProjectIn):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO projects
            (code, client_name, client_phone, client_email, client_address,
             client_site, project_type, project_date, project_timeline,
             discount, gst, notes,
             company_name, company_addr, company_phone, company_email, company_web)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """, (
            proj.code, proj.client_name, proj.client_phone, proj.client_email,
            proj.client_address, proj.client_site, proj.project_type,
            proj.project_date, proj.project_timeline,
            proj.discount, proj.gst, proj.notes,
            proj.company_name, proj.company_addr, proj.company_phone,
            proj.company_email, proj.company_web,
        ))
        project_id = cursor.lastrowid

        for ri, room in enumerate(proj.rooms):
            cursor.execute("""
                INSERT INTO rooms (project_id, type, name, sort_order)
                VALUES (%s,%s,%s,%s)
            """, (project_id, room.type, room.name, ri))
            room_id = cursor.lastrowid

            for ii, item in enumerate(room.items):
                cursor.execute("""
                    INSERT INTO items (room_id, name, custom_name, qty, length, width, rate, sort_order)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
                """, (room_id, item.name, item.custom_name, item.qty, item.length, item.width, item.rate, ii))

        conn.commit()
        return {"id": project_id, "code": proj.code, "message": "Quote saved"}

    except Exception as e:
        conn.rollback()
        if "Duplicate" in str(e):
            raise HTTPException(400, f"Quote code '{proj.code}' already exists")
        raise HTTPException(500, str(e))
    finally:
        cursor.close()
        conn.close()


@app.get("/api/quotes")
def list_quotes():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT id, code, client_name, project_type,
                   DATE_FORMAT(created_at, '%%Y-%%m-%%d %%H:%%i') as created_at
            FROM projects
            ORDER BY created_at DESC
        """)
        rows = cursor.fetchall()
        return rows
    finally:
        cursor.close()
        conn.close()


@app.get("/api/quotes/{code}")
def get_quote(code: str):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM projects WHERE code = %s", (code,))
        proj = cursor.fetchone()
        if not proj:
            raise HTTPException(404, "Quote not found")

        cursor.execute("SELECT * FROM rooms WHERE project_id = %s ORDER BY sort_order", (proj['id'],))
        rooms = cursor.fetchall()

        for room in rooms:
            cursor.execute("SELECT * FROM items WHERE room_id = %s ORDER BY sort_order", (room['id'],))
            room['items'] = cursor.fetchall()

        proj['rooms'] = rooms
        for f in ('created_at', 'updated_at'):
            if isinstance(proj.get(f), date):
                proj[f] = str(proj[f])
        return proj

    finally:
        cursor.close()
        conn.close()


@app.delete("/api/quotes/{code}")
def delete_quote(code: str):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM projects WHERE code = %s", (code,))
        conn.commit()
        if cursor.rowcount == 0:
            raise HTTPException(404, "Quote not found")
        return {"message": "Deleted"}
    finally:
        cursor.close()
        conn.close()


@app.put("/api/quotes/{code}")
def update_quote(code: str, proj: ProjectIn):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT id FROM projects WHERE code = %s", (code,))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(404, "Quote not found")
        project_id = row[0]

        cursor.execute("""
            UPDATE projects SET
                client_name=%s, client_phone=%s, client_email=%s, client_address=%s,
                client_site=%s, project_type=%s, project_date=%s, project_timeline=%s,
                discount=%s, gst=%s, notes=%s,
                company_name=%s, company_addr=%s, company_phone=%s, company_email=%s, company_web=%s
            WHERE id=%s
        """, (
            proj.client_name, proj.client_phone, proj.client_email,
            proj.client_address, proj.client_site, proj.project_type,
            proj.project_date, proj.project_timeline,
            proj.discount, proj.gst, proj.notes,
            proj.company_name, proj.company_addr, proj.company_phone,
            proj.company_email, proj.company_web,
            project_id,
        ))

        cursor.execute("DELETE FROM rooms WHERE project_id = %s", (project_id,))
        for ri, room in enumerate(proj.rooms):
            cursor.execute("""
                INSERT INTO rooms (project_id, type, name, sort_order)
                VALUES (%s,%s,%s,%s)
            """, (project_id, room.type, room.name, ri))
            room_id = cursor.lastrowid
            for ii, item in enumerate(room.items):
                cursor.execute("""
                    INSERT INTO items (room_id, name, custom_name, qty, length, width, rate, sort_order)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
                """, (room_id, item.name, item.custom_name, item.qty, item.length, item.width, item.rate, ii))

        conn.commit()
        return {"message": "Updated"}

    except Exception as e:
        conn.rollback()
        raise HTTPException(500, str(e))
    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
