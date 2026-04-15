"""
Event Planning AI MCP Server
Event management tools powered by MEOK AI Labs.
"""


import sys, os
sys.path.insert(0, os.path.expanduser('~/clawd/meok-labs-engine/shared'))
from auth_middleware import check_access

import time
import math
from datetime import date, datetime, timedelta
from collections import defaultdict
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("event-planning-ai", instructions="MEOK AI Labs MCP Server")

_call_counts: dict[str, list[float]] = defaultdict(list)
FREE_TIER_LIMIT = 30
WINDOW = 86400


def _check_rate_limit(tool_name: str) -> None:
    now = time.time()
    _call_counts[tool_name] = [t for t in _call_counts[tool_name] if now - t < WINDOW]
    if len(_call_counts[tool_name]) >= FREE_TIER_LIMIT:
        raise ValueError(f"Rate limit exceeded for {tool_name}. Free tier: {FREE_TIER_LIMIT}/day.")
    _call_counts[tool_name].append(now)


VENUE_LAYOUTS = {
    "theater": {"sqm_per_person": 0.75, "description": "Rows of chairs facing a stage"},
    "classroom": {"sqm_per_person": 1.5, "description": "Tables and chairs in rows"},
    "banquet": {"sqm_per_person": 1.4, "description": "Round tables with chairs"},
    "reception": {"sqm_per_person": 0.6, "description": "Standing/cocktail style"},
    "boardroom": {"sqm_per_person": 2.5, "description": "Single large table"},
    "u_shape": {"sqm_per_person": 2.8, "description": "Tables in U-shape formation"},
    "cabaret": {"sqm_per_person": 1.8, "description": "Round tables, half-seated facing front"},
}

CATERING_COSTS_PER_HEAD = {
    "canapes": {"low": 8, "mid": 15, "high": 30},
    "buffet": {"low": 15, "mid": 28, "high": 50},
    "sit_down_2_course": {"low": 25, "mid": 45, "high": 80},
    "sit_down_3_course": {"low": 35, "mid": 60, "high": 110},
    "afternoon_tea": {"low": 12, "mid": 22, "high": 40},
    "breakfast": {"low": 8, "mid": 15, "high": 30},
    "coffee_break": {"low": 3, "mid": 6, "high": 12},
}


@mcp.tool()
def calculate_venue_capacity(
    area_sqm: float,
    layout: str = "theater",
    has_stage: bool = False,
    stage_sqm: float = 0,
    accessibility_percent: float = 15, api_key: str = "") -> dict:
    """Calculate venue capacity for different seating layouts.

    Args:
        area_sqm: Total venue floor area in square meters
        layout: Seating layout: theater, classroom, banquet, reception, boardroom, u_shape, cabaret
        has_stage: Whether the venue needs a stage area
        stage_sqm: Stage area in sqm (auto-calculated if has_stage=True and stage_sqm=0)
        accessibility_percent: Percentage of floor space reserved for aisles/accessibility (default 15%)
    """
    allowed, msg, tier = check_access(api_key)
    if not allowed:
        return {"error": msg, "upgrade_url": "https://meok.ai/pricing"}

    _check_rate_limit("calculate_venue_capacity")

    if has_stage and stage_sqm == 0:
        stage_sqm = area_sqm * 0.08

    usable_area = area_sqm - stage_sqm
    usable_area *= (1 - accessibility_percent / 100)

    results = {}
    for layout_name, config in VENUE_LAYOUTS.items():
        capacity = int(usable_area / config["sqm_per_person"])
        results[layout_name] = {
            "capacity": capacity,
            "sqm_per_person": config["sqm_per_person"],
            "description": config["description"],
        }

    primary = results.get(layout, results["theater"])

    return {
        "venue_area_sqm": area_sqm,
        "usable_area_sqm": round(usable_area, 1),
        "stage_area_sqm": stage_sqm,
        "accessibility_reserved": f"{accessibility_percent}%",
        "recommended_layout": layout,
        "recommended_capacity": primary["capacity"],
        "all_layouts": results,
        "fire_safety_note": "Check local fire regulations for maximum occupancy. These are layout-based estimates.",
    }


@mcp.tool()
def plan_budget(
    event_type: str,
    guest_count: int,
    budget_total: float = 0,
    currency: str = "GBP",
    items: list[dict] | None = None,
    include_contingency: bool = True, api_key: str = "") -> dict:
    """Create an event budget plan with cost breakdowns and tracking.

    Args:
        event_type: Type: conference, wedding, corporate, party, charity_gala, workshop
        guest_count: Expected number of guests
        budget_total: Total budget (if 0, estimates are provided)
        currency: Currency code
        items: Custom budget items: list of dicts with keys: category, description, cost, quantity (optional)
        include_contingency: Add 10% contingency buffer
    """
    allowed, msg, tier = check_access(api_key)
    if not allowed:
        return {"error": msg, "upgrade_url": "https://meok.ai/pricing"}

    _check_rate_limit("plan_budget")

    typical_splits = {
        "conference": {"venue": 0.30, "catering": 0.25, "av_equipment": 0.15, "speakers": 0.10, "marketing": 0.08, "staff": 0.07, "printing": 0.05},
        "wedding": {"venue": 0.25, "catering": 0.35, "photography": 0.10, "flowers_decor": 0.08, "entertainment": 0.08, "attire": 0.07, "stationery": 0.04, "transport": 0.03},
        "corporate": {"venue": 0.25, "catering": 0.30, "av_equipment": 0.12, "entertainment": 0.10, "decor": 0.08, "staff": 0.08, "marketing": 0.07},
        "party": {"venue": 0.30, "catering": 0.30, "entertainment": 0.15, "decor": 0.10, "drinks": 0.10, "other": 0.05},
        "charity_gala": {"venue": 0.25, "catering": 0.30, "entertainment": 0.10, "auction_setup": 0.08, "decor": 0.10, "marketing": 0.10, "staff": 0.07},
        "workshop": {"venue": 0.35, "catering": 0.20, "materials": 0.15, "facilitators": 0.15, "av_equipment": 0.10, "printing": 0.05},
    }

    splits = typical_splits.get(event_type, typical_splits["corporate"])

    if items:
        budget_items = []
        total_cost = 0
        for item in items:
            qty = item.get("quantity", 1)
            cost = float(item.get("cost", 0)) * qty
            total_cost += cost
            budget_items.append({
                "category": item.get("category", "Other"),
                "description": item.get("description", "Item"),
                "unit_cost": float(item.get("cost", 0)),
                "quantity": qty,
                "total_cost": round(cost, 2),
            })
    else:
        per_head_estimate = {"conference": 80, "wedding": 150, "corporate": 90, "party": 40, "charity_gala": 120, "workshop": 50}
        per_head = per_head_estimate.get(event_type, 80)
        estimated_total = per_head * guest_count
        if budget_total > 0:
            estimated_total = budget_total

        budget_items = []
        total_cost = 0
        for category, pct in splits.items():
            cost = round(estimated_total * pct, 2)
            total_cost += cost
            budget_items.append({
                "category": category.replace("_", " ").title(),
                "percentage": f"{pct * 100:.0f}%",
                "total_cost": cost,
                "per_head": round(cost / guest_count, 2) if guest_count > 0 else 0,
            })

    contingency = round(total_cost * 0.10, 2) if include_contingency else 0
    grand_total = total_cost + contingency

    status = "WITHIN_BUDGET" if budget_total == 0 or grand_total <= budget_total else "OVER_BUDGET"
    variance = round(budget_total - grand_total, 2) if budget_total > 0 else 0

    return {
        "event_type": event_type,
        "guest_count": guest_count,
        "currency": currency.upper(),
        "budget_items": budget_items,
        "subtotal": round(total_cost, 2),
        "contingency": contingency,
        "grand_total": round(grand_total, 2),
        "per_head_cost": round(grand_total / guest_count, 2) if guest_count > 0 else 0,
        "budget_limit": budget_total if budget_total > 0 else "Not set",
        "status": status,
        "variance": variance,
    }


@mcp.tool()
def optimize_schedule(
    sessions: list[dict],
    start_time: str = "09:00",
    end_time: str = "17:00",
    break_duration_min: int = 15,
    lunch_duration_min: int = 60, api_key: str = "") -> dict:
    """Optimize event schedule with breaks, room assignments, and time slots.

    Args:
        sessions: List of dicts with keys: title, duration_min, speaker (optional), priority (1-5, optional), room (optional)
        start_time: Event start time (HH:MM)
        end_time: Event end time (HH:MM)
        break_duration_min: Break duration in minutes
        lunch_duration_min: Lunch break duration in minutes
    """
    allowed, msg, tier = check_access(api_key)
    if not allowed:
        return {"error": msg, "upgrade_url": "https://meok.ai/pricing"}

    _check_rate_limit("optimize_schedule")

    start_dt = datetime.strptime(start_time, "%H:%M")
    end_dt = datetime.strptime(end_time, "%H:%M")
    total_minutes = int((end_dt - start_dt).total_seconds() / 60)

    # Sort by priority (highest first)
    sorted_sessions = sorted(sessions, key=lambda s: -s.get("priority", 3))

    schedule = []
    current_time = start_dt
    session_time_used = 0
    session_count = 0
    lunch_placed = False

    for session in sorted_sessions:
        duration = int(session.get("duration_min", 30))

        # Check if it's lunch time (around midday)
        if not lunch_placed and current_time.hour >= 12:
            schedule.append({
                "time": current_time.strftime("%H:%M"),
                "end_time": (current_time + timedelta(minutes=lunch_duration_min)).strftime("%H:%M"),
                "title": "Lunch Break",
                "duration_min": lunch_duration_min,
                "type": "break",
            })
            current_time += timedelta(minutes=lunch_duration_min)
            lunch_placed = True

        # Check if session fits before end time
        if current_time + timedelta(minutes=duration) > end_dt:
            schedule.append({
                "title": session.get("title"),
                "status": "COULD_NOT_SCHEDULE",
                "reason": "Exceeds end time",
            })
            continue

        schedule.append({
            "time": current_time.strftime("%H:%M"),
            "end_time": (current_time + timedelta(minutes=duration)).strftime("%H:%M"),
            "title": session.get("title"),
            "speaker": session.get("speaker", "TBC"),
            "duration_min": duration,
            "room": session.get("room", "Main Hall"),
            "type": "session",
        })
        session_time_used += duration
        session_count += 1
        current_time += timedelta(minutes=duration)

        # Add break between sessions
        if current_time + timedelta(minutes=break_duration_min) < end_dt:
            schedule.append({
                "time": current_time.strftime("%H:%M"),
                "end_time": (current_time + timedelta(minutes=break_duration_min)).strftime("%H:%M"),
                "title": "Break",
                "duration_min": break_duration_min,
                "type": "break",
            })
            current_time += timedelta(minutes=break_duration_min)

    return {
        "date": date.today().isoformat(),
        "start_time": start_time,
        "end_time": end_time,
        "total_available_minutes": total_minutes,
        "session_time_minutes": session_time_used,
        "sessions_scheduled": session_count,
        "sessions_total": len(sessions),
        "schedule": schedule,
    }


@mcp.tool()
def manage_guest_list(
    guests: list[dict],
    table_size: int = 10,
    vip_priority: bool = True, api_key: str = "") -> dict:
    """Manage guest list with RSVP tracking, dietary needs, and table assignments.

    Args:
        guests: List of dicts with keys: name, rsvp (yes/no/pending), dietary (optional), vip (bool, optional), group (optional), plus_one (bool, optional)
        table_size: Seats per table
        vip_priority: Seat VIPs at front tables
    """
    allowed, msg, tier = check_access(api_key)
    if not allowed:
        return {"error": msg, "upgrade_url": "https://meok.ai/pricing"}

    _check_rate_limit("manage_guest_list")

    total = len(guests)
    confirmed = [g for g in guests if g.get("rsvp", "").lower() == "yes"]
    declined = [g for g in guests if g.get("rsvp", "").lower() == "no"]
    pending = [g for g in guests if g.get("rsvp", "").lower() not in ("yes", "no")]

    plus_ones = sum(1 for g in confirmed if g.get("plus_one", False))
    total_attending = len(confirmed) + plus_ones

    # Dietary tracking
    dietary_counts = defaultdict(int)
    for g in confirmed:
        diet = g.get("dietary", "standard").lower()
        dietary_counts[diet] += 1
        if g.get("plus_one"):
            dietary_counts["standard"] += 1

    # Table assignment
    tables = []
    table_num = 1
    vips = [g for g in confirmed if g.get("vip", False)]
    regulars = [g for g in confirmed if not g.get("vip", False)]

    guests_to_seat = (vips + regulars) if vip_priority else confirmed
    current_table = []

    for guest in guests_to_seat:
        seats_needed = 2 if guest.get("plus_one") else 1
        if len(current_table) + seats_needed > table_size:
            tables.append({
                "table": table_num,
                "guests": current_table,
                "seats_used": len(current_table),
                "seats_available": table_size - len(current_table),
            })
            table_num += 1
            current_table = []

        entry = {"name": guest["name"]}
        if guest.get("vip"):
            entry["vip"] = True
        if guest.get("dietary") and guest["dietary"].lower() != "standard":
            entry["dietary"] = guest["dietary"]
        current_table.append(entry)
        if guest.get("plus_one"):
            current_table.append({"name": f"{guest['name']} +1"})

    if current_table:
        tables.append({
            "table": table_num,
            "guests": current_table,
            "seats_used": len(current_table),
            "seats_available": table_size - len(current_table),
        })

    return {
        "summary": {
            "total_invited": total,
            "confirmed": len(confirmed),
            "declined": len(declined),
            "pending": len(pending),
            "plus_ones": plus_ones,
            "total_attending": total_attending,
            "response_rate": f"{((len(confirmed) + len(declined)) / total * 100):.1f}%" if total else "0%",
        },
        "dietary_requirements": dict(dietary_counts),
        "tables_needed": len(tables),
        "table_assignments": tables,
        "pending_responses": [g["name"] for g in pending],
        "vip_guests": [g["name"] for g in vips],
    }


@mcp.tool()
def estimate_catering(
    guest_count: int,
    meal_type: str = "buffet",
    quality_tier: str = "mid",
    dietary_split: dict | None = None,
    drinks_package: bool = True,
    currency: str = "GBP", api_key: str = "") -> dict:
    """Estimate catering costs and quantities for an event.

    Args:
        guest_count: Number of guests to cater for
        meal_type: Meal style: canapes, buffet, sit_down_2_course, sit_down_3_course, afternoon_tea, breakfast, coffee_break
        quality_tier: Budget tier: low, mid, high
        dietary_split: Dict of dietary percentages, e.g. {"vegetarian": 20, "vegan": 10, "gluten_free": 5}
        drinks_package: Include drinks in estimate
        currency: Currency code
    """
    allowed, msg, tier = check_access(api_key)
    if not allowed:
        return {"error": msg, "upgrade_url": "https://meok.ai/pricing"}

    _check_rate_limit("estimate_catering")

    costs = CATERING_COSTS_PER_HEAD.get(meal_type, CATERING_COSTS_PER_HEAD["buffet"])
    per_head = costs.get(quality_tier, costs["mid"])
    food_cost = per_head * guest_count

    drinks_cost = 0
    if drinks_package:
        drinks_per_head = {"low": 8, "mid": 18, "high": 35}
        drinks_cost = drinks_per_head.get(quality_tier, 18) * guest_count

    service_charge = (food_cost + drinks_cost) * 0.125
    total = food_cost + drinks_cost + service_charge

    dietary_split = dietary_split or {"vegetarian": 15, "vegan": 8, "gluten_free": 5}
    dietary_breakdown = {}
    standard_pct = 100
    for diet, pct in dietary_split.items():
        count = max(1, round(guest_count * pct / 100))
        dietary_breakdown[diet] = count
        standard_pct -= pct
    dietary_breakdown["standard"] = max(0, round(guest_count * standard_pct / 100))

    quantity_guide = {
        "canapes": f"{guest_count * 8}-{guest_count * 10} pieces (8-10 per person)",
        "buffet": f"Plan for {math.ceil(guest_count * 1.1)} servings (10% buffer)",
        "sit_down_2_course": f"{guest_count} plated meals",
        "sit_down_3_course": f"{guest_count} plated meals",
        "afternoon_tea": f"{guest_count} tea sets, {guest_count * 6} finger sandwiches/cakes",
        "coffee_break": f"{math.ceil(guest_count * 1.2)} hot drinks, {guest_count} pastries",
    }

    return {
        "guest_count": guest_count,
        "meal_type": meal_type,
        "quality_tier": quality_tier,
        "currency": currency.upper(),
        "cost_breakdown": {
            "food_per_head": per_head,
            "food_total": round(food_cost, 2),
            "drinks_per_head": round(drinks_cost / guest_count, 2) if guest_count else 0,
            "drinks_total": round(drinks_cost, 2),
            "service_charge": round(service_charge, 2),
        },
        "total_estimate": round(total, 2),
        "per_head_total": round(total / guest_count, 2) if guest_count else 0,
        "dietary_breakdown": dietary_breakdown,
        "quantity_guide": quantity_guide.get(meal_type, "Contact caterer for guidance"),
        "tips": [
            "Confirm final numbers 48-72 hours before the event",
            "Order 5-10% extra for unexpected guests",
            "Ensure all allergens are labeled at serving stations",
        ],
    }


if __name__ == "__main__":
    mcp.run()
