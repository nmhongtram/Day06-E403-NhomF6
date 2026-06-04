"""
Scoring — pure Python algorithms, no LLM.
"""

from .mock_db import (
    DESTINATIONS, RESORTS, get_resorts_by_destination,
    get_rooms_by_resort, get_booking_by_ref, get_user_bookings,
    get_availability_grid, compute_refund, CANCELLATION_POLICIES,
)


# ── MATCH SCORING ─────────────────────────────────────────────────────────────

_DEST_NAME_ALIASES: dict[str, list[str]] = {
    "pq":  ["phú quốc", "phu quoc"],
    "nt":  ["nha trang"],
    "dn":  ["hội an", "hoi an", "quảng nam", "quang nam", "đà nẵng", "da nang"],
    "hl":  ["hạ long", "ha long", "quảng ninh", "quang ninh"],
    "ht":  ["hà tĩnh", "ha tinh", "cửa sót", "cua sot"],
    "na":  ["nghệ an", "nghe an", "cửa hội", "cua hoi", "vinh"],
    "bn":  ["bắc ninh", "bac ninh"],
}


def _destination_match(dest_id: str, requested: str) -> bool:
    req = requested.lower()
    return any(a in req or req in a for a in _DEST_NAME_ALIASES.get(dest_id, []))


def score_destination(dest: dict, entities: dict) -> int:
    score = 50
    vibe = (entities.get("vibe") or "").lower()
    trip_type = (entities.get("trip_type") or "").lower()
    dest_vibes = dest.get("vibes", [])
    requested_dest = (entities.get("destination") or "").strip()

    if requested_dest:
        if _destination_match(dest.get("id", ""), requested_dest):
            score += 45
        else:
            score -= 15

    if vibe and vibe in dest_vibes:
        score += 25

    if trip_type == "family" and "family" in dest_vibes:
        score += 15
    elif trip_type == "couple" and "couple" in dest_vibes:
        score += 15

    flight = dest.get("flight_from_hcm_minutes", 120)
    if flight <= 60:
        score += 10
    elif flight <= 90:
        score += 5

    return min(max(score, 5), 99)


def score_resort(resort: dict, entities: dict) -> int:
    score = 50
    vibe = (entities.get("vibe") or "").lower()
    trip_type = (entities.get("trip_type") or "").lower()
    guest_count = entities.get("guest_count") or 2
    budget = entities.get("budget")
    attrs = resort.get("attributes", [])

    if vibe and vibe in attrs:
        score += 20
    if trip_type == "family" and ("family" in attrs or "kids_club" in attrs):
        score += 20
    elif trip_type == "couple" and "couple" in attrs:
        score += 20
    if resort.get("max_guests", 4) >= guest_count:
        score += 15
    if budget:
        if resort["price_from"] <= budget / 2:
            score += 10
        elif resort["price_from"] <= budget:
            score += 5
    score += min(int((resort.get("rating", 4.0) - 4.0) * 20), 10)
    return min(score, 99)


def score_room(room: dict, entities: dict) -> int:
    score = 40
    guest_count = entities.get("guest_count") or 2
    vibe = (entities.get("vibe") or "").lower()
    trip_type = (entities.get("trip_type") or "").lower()
    budget = entities.get("budget")
    attrs = room.get("attributes", [])
    capacity = room.get("capacity", 2)

    if capacity >= guest_count:
        score += 25
        if capacity == guest_count:
            score += 10
    if trip_type == "family" and "family" in attrs:
        score += 15
    elif trip_type == "couple" and "couple" in attrs:
        score += 15
    if vibe == "beach" and ("ocean_view" in attrs or "beach_access" in attrs):
        score += 10
    if budget:
        nights = entities.get("nights") or 2
        if room.get("price_per_night", 999_999_999) * nights <= budget:
            score += 15
    return min(score, 99)


def get_recommendation_reasons(item: dict, entities: dict, item_type: str) -> list[str]:
    reasons = []
    guest_count = entities.get("guest_count") or 2
    vibe = (entities.get("vibe") or "").lower()
    trip_type = (entities.get("trip_type") or "").lower()
    budget = entities.get("budget")

    if item_type == "destination":
        vibes = item.get("vibes", [])
        flight = item.get("flight_from_hcm_minutes", 120)
        if "beach" in vibes and vibe == "beach":
            reasons.append("Biển đẹp, đúng theo sở thích của bạn")
        if "family" in vibes and trip_type == "family":
            reasons.append("Thân thiện với gia đình có trẻ em")
        if flight <= 60:
            reasons.append(f"Bay từ TP.HCM chỉ {flight} phút")
        if budget:
            reasons.append("Trong khoảng ngân sách bạn chọn")
        if not reasons:
            reasons.append(item.get("description", "Điểm đến nổi tiếng của Vinpearl")[:60])

    elif item_type == "resort":
        attrs = item.get("attributes", [])
        if "kids_club" in attrs and trip_type == "family":
            reasons.append("Có Kids Club cho bé")
        if "beach" in attrs:
            reasons.append("Gần biển, view đẹp")
        if "all_inclusive" in attrs:
            reasons.append("Gói All-inclusive tiện lợi")
        if item.get("rating", 0) >= 4.8:
            reasons.append(f"Đánh giá xuất sắc ⭐ {item['rating']}")
        if guest_count >= 4 and item.get("max_guests", 0) >= guest_count:
            reasons.append(f"Phù hợp cho nhóm {guest_count} người")

    elif item_type == "room":
        attrs = item.get("attributes", [])
        capacity = item.get("capacity", 2)
        if capacity >= guest_count:
            reasons.append(f"Phù hợp {guest_count} người ({capacity} người tối đa)")
        if "extra_bed" in attrs:
            reasons.append("Extra bed miễn phí cho bé")
        if "pool_view" in attrs:
            reasons.append("View hồ bơi đẹp")
        if "ocean_view" in attrs or "beach_access" in attrs:
            reasons.append("View biển trực tiếp")
        if "kitchenette" in attrs:
            reasons.append("Có bếp nhỏ tiện cho gia đình")
        if budget:
            nights = entities.get("nights") or 2
            if item.get("price_per_night", 0) * nights <= budget:
                reasons.append("Tổng trong ngân sách bạn đề ra")

    return reasons[:4] or ["Phù hợp với nhu cầu của bạn"]


# ── AGGREGATED QUERIES ────────────────────────────────────────────────────────

def query_and_score_destinations(entities: dict) -> list[dict]:
    results = []
    for dest in DESTINATIONS.values():
        score = score_destination(dest, entities)
        reasons = get_recommendation_reasons(dest, entities, "destination")
        results.append({**dest, "match_score": score, "reasons": reasons})
    results.sort(key=lambda x: x["match_score"], reverse=True)
    return results[:3]


def resolve_destination_id(destination_name: str) -> str | None:
    lower = destination_name.lower().strip()
    for dest_id, aliases in _DEST_NAME_ALIASES.items():
        if any(a in lower or lower in a for a in aliases):
            return dest_id
    return None


def query_and_score_resorts(destination_id: str, entities: dict) -> list[dict]:
    resorts = get_resorts_by_destination(destination_id)
    results = []
    for resort in resorts:
        score = score_resort(resort, entities)
        reasons = get_recommendation_reasons(resort, entities, "resort")
        results.append({**resort, "match_score": score, "ai_pick": score >= 90, "reasons": reasons})
    results.sort(key=lambda x: x["match_score"], reverse=True)
    if results and not any(r["ai_pick"] for r in results):
        results[0]["ai_pick"] = True
    return results[:3]


def query_and_score_rooms(resort_id: str, entities: dict) -> list[dict]:
    rooms = get_rooms_by_resort(resort_id)
    results = []
    for room in rooms:
        score = score_room(room, entities)
        reasons = get_recommendation_reasons(room, entities, "room")
        results.append({**room, "match_score": score, "ai_pick": score >= 90, "reasons": reasons})
    results.sort(key=lambda x: x["match_score"], reverse=True)
    if results and not any(r["ai_pick"] for r in results):
        results[0]["ai_pick"] = True
    return results


def get_booking_and_availability(user_message: str, user_id: str, entities: dict) -> dict | None:
    booking_ref = entities.get("booking_ref")
    booking = get_booking_by_ref(booking_ref, user_id) if booking_ref else None
    if not booking:
        bookings = get_user_bookings(user_id)
        booking = bookings[0] if bookings else None
    if not booking:
        return None
    policy = CANCELLATION_POLICIES["default"]["change_policy"]
    dates = get_availability_grid(booking["resort_id"], booking["room_id"], booking["checkin"])
    return {"booking": booking, "change_policy": policy, "available_dates": dates}


def get_booking_and_refund(user_message: str, user_id: str, entities: dict) -> dict | None:
    booking_ref = entities.get("booking_ref")
    booking = get_booking_by_ref(booking_ref, user_id) if booking_ref else None
    if not booking:
        bookings = get_user_bookings(user_id)
        booking = bookings[0] if bookings else None
    if not booking:
        return None
    refund = compute_refund(booking["total_paid"], booking["checkin"])
    return {"booking": booking, "refund": refund, "policy_tiers": CANCELLATION_POLICIES["default"]["tiers"]}
