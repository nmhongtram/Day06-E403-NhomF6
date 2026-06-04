"""
Mock Database — MyVinpearl AI Booking Assistant
Dữ liệu mô phỏng theo PROTOTYPE_PROMPT.md Section 17 & Appendix
"""

import json
from pathlib import Path
from datetime import date, timedelta

# ── DESTINATIONS ──────────────────────────────────────────────────────────────

DESTINATIONS = {
    "pq": {
        "id": "pq",
        "name": "Phú Quốc",
        "region": "Miền Nam",
        "vibes": ["beach", "family", "resort", "island"],
        "flight_from_hcm_minutes": 60,
        "image": "https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=600&q=80",
        "rating": 4.8,
        "description": "Đảo ngọc phía Tây Nam, biển xanh cát trắng, lý tưởng cho gia đình.",
    },
    "dn": {
        "id": "dn",
        "name": "Hội An",
        "region": "Miền Trung",
        "vibes": ["beach", "culture", "couple", "family", "golf"],
        "flight_from_hcm_minutes": 75,
        "image": "https://images.unsplash.com/photo-1559592413-7cec4d0cae2b?w=600&q=80",
        "rating": 4.7,
        "description": "Phố cổ UNESCO, biển An Bàng đẹp, sân golf đẳng cấp.",
    },
    "nt": {
        "id": "nt",
        "name": "Nha Trang",
        "region": "Miền Trung",
        "vibes": ["beach", "couple", "diving", "nightlife", "island"],
        "flight_from_hcm_minutes": 55,
        "image": "https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=600&q=80",
        "rating": 4.6,
        "description": "Vịnh biển đẹp, nhiều hoạt động lặn biển và thể thao nước.",
    },
    "hl": {
        "id": "hl",
        "name": "Hạ Long",
        "region": "Miền Bắc",
        "vibes": ["nature", "cruise", "family", "couple"],
        "flight_from_hcm_minutes": 120,
        "image": "https://images.unsplash.com/photo-1573843981267-be1999ff37cd?w=600&q=80",
        "rating": 4.7,
        "description": "Di sản thiên nhiên thế giới, vịnh đảo vôi hùng vĩ.",
    },
    "ht": {
        "id": "ht",
        "name": "Hà Tĩnh",
        "region": "Miền Trung",
        "vibes": ["beach", "nature", "family", "eco"],
        "flight_from_hcm_minutes": 80,
        "image": "https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=600&q=80",
        "rating": 4.4,
        "description": "Bờ biển Cửa Sót hoang sơ, thiên nhiên yên bình.",
    },
    "na": {
        "id": "na",
        "name": "Nghệ An",
        "region": "Miền Trung",
        "vibes": ["beach", "nature", "family"],
        "flight_from_hcm_minutes": 85,
        "image": "https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=600&q=80",
        "rating": 4.4,
        "description": "Biển Cửa Hội xinh đẹp, gần thành phố Vinh.",
    },
    "bn": {
        "id": "bn",
        "name": "Bắc Ninh",
        "region": "Miền Bắc",
        "vibes": ["city", "culture", "business"],
        "flight_from_hcm_minutes": 115,
        "image": "https://images.unsplash.com/photo-1571896349842-33c89424de2d?w=600&q=80",
        "rating": 4.3,
        "description": "Vùng đất Kinh Bắc, gần Hà Nội, thuận tiện công tác.",
    },
}

# ── RESORTS & ROOMS — loaded from data/hotels.json ────────────────────────────

# codebase/src/utils/mock_db.py → codebase/data/hotels.json
_HOTEL_DATA_PATH = Path(__file__).parent.parent.parent / "data" / "hotels.json"

def _load_hotel_data():
    with open(_HOTEL_DATA_PATH, encoding="utf-8") as f:
        data = json.load(f)
    resorts: dict = {}
    rooms: dict = {}
    for hotel in data.get("hotels", []):
        resort = {k: v for k, v in hotel.items() if k != "rooms"}
        resort["price_from"] = hotel.get("price", 0)
        resort["star"] = hotel.get("star", 4)
        resorts[hotel["id"]] = resort

        hotel_rooms = []
        for room in hotel.get("rooms", []):
            entry = {**room, "resort_id": hotel["id"], "price_per_night": room.get("price", 0)}
            hotel_rooms.append(entry)
        rooms[hotel["id"]] = hotel_rooms
    return resorts, rooms


RESORTS, ROOMS = _load_hotel_data()


# ── MOCK BOOKINGS ─────────────────────────────────────────────────────────────

MOCK_BOOKINGS = [
    {
        "id": "book_001",
        "ref": "VNP-2024-8821",
        "user_id": "demo_user",
        "resort_id": "vpww",
        "resort_name": "Vinpearl Wonderworld Phú Quốc",
        "destination": "Phú Quốc",
        "room_id": "fs_vpww",
        "room_type": "Biệt Thự 2 Phòng Ngủ",
        "checkin": "2024-06-20",
        "checkout": "2024-06-22",
        "nights": 2,
        "guests": 4,
        "total_paid": 6_954_000,
        "status": "confirmed",
        "image": "https://images.unsplash.com/photo-1540541338537-44a2b28e84f3?w=600&q=80",
    },
    {
        "id": "book_002",
        "ref": "VNP-2024-7753",
        "user_id": "demo_user",
        "resort_id": "vprg_dn",
        "resort_name": "Vinpearl Resort & Golf Nam Hội An",
        "destination": "Hội An",
        "room_id": "dlx_vprg_dn",
        "room_type": "Deluxe Golf View",
        "checkin": "2024-07-15",
        "checkout": "2024-07-18",
        "nights": 3,
        "guests": 2,
        "total_paid": 8_400_000,
        "status": "confirmed",
        "image": "https://images.unsplash.com/photo-1559592413-7cec4d0cae2b?w=600&q=80",
    },
]

# ── CANCELLATION POLICIES ────────────────────────────────────────────────────

CANCELLATION_POLICIES = {
    "default": {
        "tiers": [
            {"days_min": 15, "days_max": 999, "fee_pct": 10,  "label": "15+ ngày trước"},
            {"days_min": 8,  "days_max": 14,  "fee_pct": 30,  "label": "8–14 ngày trước"},
            {"days_min": 3,  "days_max": 7,   "fee_pct": 50,  "label": "3–7 ngày trước"},
            {"days_min": 0,  "days_max": 2,   "fee_pct": 100, "label": "0–2 ngày trước"},
        ],
        "change_policy": {
            "allowed": True,
            "free_change_before_days": 7,
            "change_fee": 300_000,
            "max_changes": 2,
        },
    }
}

# ── AVAILABILITY DATA ─────────────────────────────────────────────────────────

_BOOKED_DATES: dict[str, dict[str, list[str]]] = {
    # ── Nha Trang ──────────────────────────────────────────────────────────────
    "vprs_nt": {
        "dlx_vprs_nt":   ["2026-06-06","2026-06-07","2026-06-13","2026-06-14","2026-06-20","2026-06-21","2026-06-27","2026-06-28"],
        "fam_vprs_nt":   ["2026-06-07","2026-06-14","2026-06-21","2026-06-28"],
        "villa_vprs_nt": ["2026-06-06","2026-06-07","2026-06-08"],
    },
    "vpl_nt": {
        "prem_vpl_nt":   ["2026-06-06","2026-06-07","2026-06-13","2026-06-14","2026-06-20","2026-06-21"],
        "suite_vpl_nt":  ["2026-06-07","2026-06-14","2026-06-20","2026-06-21","2026-06-27","2026-06-28"],
        "villa2_vpl_nt": ["2026-06-06","2026-06-07"],
    },
    "vpr_nt": {
        "std_vpr_nt":    ["2026-06-06","2026-06-07","2026-06-08","2026-06-13","2026-06-14","2026-06-15","2026-06-20","2026-06-21","2026-06-27","2026-06-28"],
        "fam_vpr_nt":    ["2026-06-06","2026-06-07","2026-06-13","2026-06-14"],
        "suite_vpr_nt":  ["2026-06-06","2026-06-07"],
    },
    "vpbf_nt": {
        "dlx_vpbf_nt":   ["2026-06-06","2026-06-07","2026-06-08","2026-06-09","2026-06-13","2026-06-14","2026-06-20","2026-06-21","2026-06-27","2026-06-28"],
        "fam_vpbf_nt":   ["2026-06-06","2026-06-07","2026-06-08","2026-06-13","2026-06-14","2026-06-21"],
    },
    "htr_nt": {
        "bung_htr_nt":   ["2026-06-07","2026-06-14","2026-06-21","2026-06-28"],
        "vbung_htr_nt":  ["2026-06-06","2026-06-07","2026-06-13","2026-06-14"],
        "villa_htr_nt":  [],
    },
    "vpe_nt": {
        "dlx_vpe_nt":    ["2026-06-06","2026-06-07","2026-06-13","2026-06-14","2026-06-20","2026-06-21"],
        "suite_vpe_nt":  ["2026-06-06","2026-06-07"],
    },
    # ── Phú Quốc ──────────────────────────────────────────────────────────────
    "vpww": {
        "dlx_vpww":      ["2026-06-06","2026-06-07","2026-06-13","2026-06-14","2026-06-20","2026-06-21","2026-06-27","2026-06-28"],
        "fs_vpww":       ["2026-06-07","2026-06-14","2026-06-21"],
        "villa3_vpww":   ["2026-06-06","2026-06-07"],
        "villa4_vpww":   [],
    },
    # ── Hội An ────────────────────────────────────────────────────────────────
    "vprg_dn": {
        "dlx_vprg_dn":   ["2026-06-06","2026-06-07","2026-06-13","2026-06-14","2026-06-20","2026-06-21"],
        "golf_vprg_dn":  ["2026-06-06","2026-06-07","2026-06-14"],
        "villa_vprg_dn": ["2026-06-07","2026-06-14","2026-06-21"],
        "pv_vprg_dn":    ["2026-06-06","2026-06-07"],
    },
    # ── Hạ Long ───────────────────────────────────────────────────────────────
    "vprs_hl": {
        "dlx_vprs_hl":   ["2026-06-06","2026-06-07","2026-06-13","2026-06-14","2026-06-20","2026-06-21"],
        "fam_vprs_hl":   ["2026-06-07","2026-06-14","2026-06-21"],
        "villa_vprs_hl": ["2026-06-06","2026-06-07"],
        "suite_vprs_hl": [],
    },
}


def check_room_available(hotel_id: str, room_id: str, date_iso: str) -> bool:
    booked = _BOOKED_DATES.get(hotel_id, {}).get(room_id, [])
    return date_iso not in booked


def get_hotel_availability(hotel_id: str, start_iso: str, nights: int = 14) -> list[dict]:
    try:
        start = date.fromisoformat(start_iso)
    except Exception:
        start = date.today()

    hotel_rooms = ROOMS.get(hotel_id, [])
    hotel_booked = _BOOKED_DATES.get(hotel_id, {})

    day_names = ["T.2", "T.3", "T.4", "T.5", "T.6", "T.7", "CN"]
    result = []
    for i in range(nights):
        d = start + timedelta(days=i)
        d_iso = d.isoformat()
        any_avail = any(
            d_iso not in hotel_booked.get(r["id"], [])
            for r in hotel_rooms
        )
        is_weekend = d.weekday() >= 5
        result.append({
            "date": d.strftime("%d/%m"),
            "date_iso": d_iso,
            "day": day_names[d.weekday()],
            "available": any_avail,
            "is_weekend": is_weekend,
            "label": "Còn phòng" if any_avail else "Hết phòng",
        })
    return result


def get_availability_grid(resort_id: str, room_id: str, anchor_date_str: str) -> list:
    try:
        anchor = date.fromisoformat(anchor_date_str)
    except Exception:
        anchor = date(2026, 6, 20)

    day_names = ["T.2", "T.3", "T.4", "T.5", "T.6", "T.7", "CN"]
    result = []
    for offset in range(-1, 8):
        d = anchor + timedelta(days=offset)
        d_iso = d.isoformat()
        available = check_room_available(resort_id, room_id, d_iso)
        is_weekend = d.weekday() >= 5
        delta = 300_000 if is_weekend and available else 0

        result.append({
            "date": d.strftime("%d/%m"),
            "date_iso": d_iso,
            "day": day_names[d.weekday()],
            "available": available,
            "price_delta": delta,
            "label": "Còn phòng" if available else "Hết phòng",
            "is_current": offset == 0,
        })
    return result


def get_booking_by_ref(ref: str, user_id: str = "demo_user") -> dict | None:
    for b in MOCK_BOOKINGS:
        if b["ref"].upper() == ref.upper() and b["user_id"] == user_id:
            return b
    return None

def get_user_bookings(user_id: str = "demo_user") -> list:
    return [b for b in MOCK_BOOKINGS if b["user_id"] == user_id]

def get_resorts_by_destination(destination_id: str) -> list:
    return [r for r in RESORTS.values() if r["destination_id"] == destination_id]

def get_rooms_by_resort(resort_id: str) -> list:
    return ROOMS.get(resort_id, [])


def get_available_hotels_for_dates(
    destination_id: str,
    checkin_iso: str,
    nights: int = 1,
    guest_count: int = 2,
) -> list[dict]:
    try:
        checkin = date.fromisoformat(checkin_iso)
    except Exception:
        return get_resorts_by_destination(destination_id)

    checkout = checkin + timedelta(days=max(nights, 1))
    resorts = get_resorts_by_destination(destination_id)
    result = []

    for resort in resorts:
        rooms = get_rooms_by_resort(resort["id"])
        available_rooms = []
        for room in rooms:
            if room.get("capacity", 0) < guest_count:
                continue
            room_ok = all(
                check_room_available(resort["id"], room["id"], (checkin + timedelta(days=n)).isoformat())
                for n in range(max(nights, 1))
            )
            if room_ok:
                available_rooms.append(room)

        if available_rooms:
            min_price = min(r.get("price_per_night", 0) for r in available_rooms)
            result.append({
                **resort,
                "available_rooms_count": len(available_rooms),
                "price_from": min_price,
                "checkin": checkin_iso,
                "checkout": checkout.isoformat(),
                "nights": max(nights, 1),
                "has_availability": True,
            })

    return result


def resolve_destination_id(destination_name: str) -> str | None:
    lower = destination_name.lower().strip()
    _ALIASES = {
        "pq":  ["phú quốc", "phu quoc", "phuquoc"],
        "nt":  ["nha trang", "nhatrang"],
        "dn":  ["đà nẵng", "da nang", "hội an", "hoi an", "quảng nam"],
        "hl":  ["hạ long", "ha long", "halong"],
        "ht":  ["hà tĩnh", "ha tinh"],
        "na":  ["nghệ an", "nghe an", "vinh"],
        "hue": ["huế", "hue"],
    }
    for dest_id, aliases in _ALIASES.items():
        if any(a in lower or lower in a for a in aliases):
            return dest_id
    return None

def compute_refund(total_paid: int, checkin_date_str: str, today_str: str | None = None) -> dict:
    try:
        checkin = date.fromisoformat(checkin_date_str)
        today = date.fromisoformat(today_str) if today_str else date.today()
    except Exception:
        checkin = date(2024, 6, 20)
        today = date.today()

    days_until = (checkin - today).days
    policy = CANCELLATION_POLICIES["default"]

    fee_pct = 100
    tier_label = "0–2 ngày trước"
    for tier in policy["tiers"]:
        if tier["days_min"] <= days_until <= tier["days_max"]:
            fee_pct = tier["fee_pct"]
            tier_label = tier["label"]
            break

    fee_amount = round(total_paid * fee_pct / 100)
    refund_amount = total_paid - fee_amount

    next_tier_deadline = None
    for i, tier in enumerate(policy["tiers"]):
        if days_until >= tier["days_min"]:
            if i > 0:
                next_tier_deadline = policy["tiers"][i - 1]["days_min"]
            break

    return {
        "days_until_checkin": days_until,
        "fee_pct": fee_pct,
        "fee_amount": fee_amount,
        "refund_amount": refund_amount,
        "tier_label": tier_label,
        "next_tier_deadline_days": next_tier_deadline,
        "refund_timeline": "3–5 ngày làm việc",
    }
