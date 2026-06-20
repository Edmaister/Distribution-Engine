from utils.db import get_connection
from utils.kafka import publish_event

def update_referral_progress(data):
    referral_track_id = data.get("referralTrackId")
    status = data.get("status")
    referee_ucn = data.get("refereeUCN")
    product = data.get("product")
    sub_product = data.get("subProduct")

    conn = get_connection(); cursor = conn.cursor()
    try:
        cursor.execute(
            """
            INSERT INTO referral_progress (referral_track_id, referee_ucn, status, product, sub_product)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (referral_track_id) DO UPDATE SET
                status = EXCLUDED.status,
                product = EXCLUDED.product,
                sub_product = EXCLUDED.sub_product
            """, (referral_track_id, referee_ucn, status, product, sub_product)
        )
        conn.commit()
    finally:
        cursor.close(); conn.close()

    publish_event("referral-events", {
        "eventType": "REFERRAL_PROGRESS_UPDATED",
        "referralTrackId": referral_track_id,
        "status": status,
        "product": product,
        "subProduct": sub_product,
    })
