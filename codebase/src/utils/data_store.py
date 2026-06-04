"""
Business logic layer — clean public API wrapping mock_db and scoring.
Analogous to data_store.py in reference structure.
"""

import re
from datetime import date, timedelta

from . import mock_db
from . import scoring as _scoring


# ── DESTINATION / HOTEL SEARCH ────────────────────────────────────────────────

def search_destinations(entities: dict) -> list[dict]:
    """Return top 3 destinations scored by entities (vibe, trip_type, guest_count...)."""
    return _scoring.query_and_score_destinations(entities)


def search_hotels_available(destination_id: str, checkin_iso: str, nights: int, guest_count: int) -> list[dict]:
    """Return hotels in destination that have rooms available for the full stay."""
    return mock_db.get_available_hotels_for_dates(destination_id, checkin_iso, nights, guest_count)


def get_hotels_for_destination(destination_id: str, entities: dict) -> list[dict]:
    """Return scored hotels for a destination (no date filter)."""
    return _scoring.query_and_score_resorts(destination_id, entities)


def get_hotel_rooms(hotel_id: str, entities: dict) -> list[dict]:
    """Return scored rooms for a hotel."""
    return _scoring.query_and_score_rooms(hotel_id, entities)


def resolve_destination_id(name: str) -> str | None:
    """Map 'Phú Quốc' → 'pq', etc."""
    return mock_db.resolve_destination_id(name)


# ── BOOKING LOOKUP ────────────────────────────────────────────────────────────

def get_booking(user_id: str = "demo_user", booking_ref: str = None) -> dict | None:
    if booking_ref:
        # Return None if the specific ref isn't found — don't silently return a different booking
        return mock_db.get_booking_by_ref(booking_ref, user_id)
    # Only fall back to most recent booking when NO ref is provided
    bookings = mock_db.get_user_bookings(user_id)
    return bookings[0] if bookings else None


def get_user_bookings(user_id: str = "demo_user") -> list[dict]:
    return mock_db.get_user_bookings(user_id)


# ── REFUND / AVAILABILITY ─────────────────────────────────────────────────────

def compute_refund(user_id: str = "demo_user", booking_ref: str = None) -> dict | None:
    booking = get_booking(user_id, booking_ref)
    if not booking:
        return None
    refund = mock_db.compute_refund(booking["total_paid"], booking["checkin"])
    return {"booking": booking, "refund": refund, "policy_tiers": mock_db.CANCELLATION_POLICIES["default"]["tiers"]}


def get_available_change_dates(user_id: str = "demo_user", booking_ref: str = None) -> dict | None:
    booking = get_booking(user_id, booking_ref)
    if not booking:
        return None
    dates = mock_db.get_availability_grid(booking["resort_id"], booking["room_id"], booking["checkin"])
    policy = mock_db.CANCELLATION_POLICIES["default"]["change_policy"]
    return {"booking": booking, "available_dates": dates, "change_policy": policy}


# ── BOOKING CREATION ──────────────────────────────────────────────────────────

import random
import string

def create_booking(
    hotel_id: str, room_id: str, checkin: str, checkout: str,
    guests: int, user_name: str, email: str,
) -> dict:
    """Create a mock booking and return the booking record."""
    suffix = "".join(random.choices(string.digits, k=4))
    ref = f"VNP-{date.today().year}-{suffix}"

    hotel = mock_db.RESORTS.get(hotel_id, {})
    rooms = mock_db.get_rooms_by_resort(hotel_id)
    room = next((r for r in rooms if r["id"] == room_id), {})

    try:
        nights = (date.fromisoformat(checkout) - date.fromisoformat(checkin)).days
    except Exception:
        nights = 1

    total = room.get("price_per_night", 0) * nights

    return {
        "ref": ref,
        "hotel_id": hotel_id,
        "hotel_name": hotel.get("name", hotel_id),
        "room_id": room_id,
        "room_name": room.get("name", room_id),
        "checkin": checkin,
        "checkout": checkout,
        "nights": nights,
        "guests": guests,
        "total_price": total,
        "user_name": user_name,
        "email": email,
        "status": "confirmed",
    }


# ── DATE PARSING ──────────────────────────────────────────────────────────────

def parse_checkin_date(s: str) -> str | None:
    """Parse D/M, YYYY-MM-DD, or relative phrases to ISO date string."""
    if not s:
        return None
    s = s.strip()
    if re.match(r"^\d{4}-\d{2}-\d{2}$", s):
        return s
    m = re.match(r"^(\d{1,2})[/\-](\d{1,2})(?:[/\-](\d{4}))?$", s)
    if m:
        day, month = int(m.group(1)), int(m.group(2))
        year = int(m.group(3)) if m.group(3) else date.today().year
        try:
            return date(year, month, day).isoformat()
        except ValueError:
            pass
    today = date.today()
    low = s.lower()
    if "ngày mai" in low:
        return (today + timedelta(days=1)).isoformat()
    if "cuối tuần" in low or "weekend" in low:
        return (today + timedelta(days=(5 - today.weekday()) % 7 or 7)).isoformat()
    if "tuần tới" in low or "next week" in low:
        return (today + timedelta(days=7)).isoformat()
    if "tháng sau" in low:
        nm = date(today.year + (1 if today.month == 12 else 0), today.month % 12 + 1, 1)
        return nm.isoformat()
    return None
