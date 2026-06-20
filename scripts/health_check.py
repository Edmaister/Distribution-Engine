import json
from utils.db import get_connection
from utils.kafka import publish_event
from utils.logging import get_logger

logger = get_logger(__name__)

def check_db():
    try:
        conn = get_connection()
        with conn.cursor() as cur:
            cur.execute("SELECT 1")
            _ = cur.fetchone()
        conn.close()
        return {"ok": True}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def check_kafka():
    try:
        publish_event("health-check", {"ping": "pong"})
        return {"ok": True}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def main():
    db = check_db()
    kf = check_kafka()
    result = {"db": db, "kafka": kf}
    print(json.dumps(result, ensure_ascii=False))

if __name__ == "__main__":
    main()
