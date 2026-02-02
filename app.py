import re
import io
import pandas as pd
import streamlit as st

# Day names
WEEKDAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


def clean_netid(raw: str) -> str:
# Find clean NetIDs
    if pd.isna(raw) or not isinstance(raw, str):
        return ""
    s = str(raw).strip().lower()
    s = re.sub(r"@vols\.utk\.edu\s*$", "", s, flags=re.IGNORECASE).strip()
    return s


def find_netid_column(df: pd.DataFrame) -> str | None:
# NetID {my.utk.edu}
    for col in df.columns:
        if "netid" in str(col).lower():
            return col
    return None


def find_day_columns(df: pd.DataFrame) -> list[str]:
# Day column
    found = []
    for day in WEEKDAYS:
        for col in df.columns:
            if day.lower() in str(col).lower():
                found.append(col)
                break
    return found


def parse_time_slots(cell_value) -> set[str]:
#Parse
    if pd.isna(cell_value):
        return set()
    text = str(cell_value).strip()
    if not text:
        return set()
#Split Parse
    parts = re.split(r"[,;\n]+", text)
    return {p.strip() for p in parts if p.strip()}


def build_master_schedule(df: pd.DataFrame, netid_col: str, day_cols: list[str]) -> dict[str, set[tuple[str, str]]]:
#Master Scheduler
    schedules = {}
    for _, row in df.iterrows():
        netid = clean_netid(row.get(netid_col, ""))
        if not netid:
            continue
        master = set()
        for col in day_cols:
            day = None
            for d in WEEKDAYS:
                if d.lower() in str(col).lower():
                    day = d
                    break
            if day is None:
                continue
            slots = parse_time_slots(row.get(col))
            for slot in slots:
                master.add((day, slot))
        schedules[netid] = master
    return schedules


def greedy_group(
    schedules: dict[str, set[tuple[str, str]]],
    min_group_size: int,
    max_group_size: int,
    min_common_slots: int = 1,
) -> tuple[list[tuple[list[str], set[tuple[str, str]]]], list[str]]:
# Technique "Greedy"
    if max_group_size < 1 or min_group_size > max_group_size:
        return [], list(schedules.keys())

    netids = list(schedules.keys())
    if not netids:
        return [], []

    groups: list[tuple[list[str], set[tuple[str, str]]]] = []
    manual_review: list[str] = []
    unplaced = list(netids)

    while unplaced:
        seed = unplaced.pop(0)
        group_netids = [seed]
        common = set(schedules[seed])

        while len(group_netids) < max_group_size and unplaced:
# Most common 
            best_candidate = None
            best_intersection_size = min_common_slots - 1

            for cand in unplaced:
                inter = common & schedules[cand]
                if len(inter) >= min_common_slots and len(inter) > best_intersection_size:
                    best_intersection_size = len(inter)
                    best_candidate = cand

            if best_candidate is None:
                break
            group_netids.append(best_candidate)
            common = common & schedules[best_candidate]
            unplaced.remove(best_candidate)

# Group = [min - max] and overlap
        if (
            min_group_size <= len(group_netids) <= max_group_size
            and len(common) >= min_common_slots
        ):
            groups.append((group_netids, common))
        else:
            manual_review.extend(group_netids)

    return groups, manual_review


def greedy_group_remainder(
    schedules: dict[str, set[tuple[str, str]]],
    netids: list[str],
    min_group_size: int,
    max_group_size: int,
) -> tuple[list[tuple[list[str], set[tuple[str, str]]]], list[str]]:
# Following remainder of best course effort or contact
    if not netids or max_group_size < 1 or min_group_size > max_group_size:
        return [], list(netids)

    remainder_groups: list[tuple[list[str], set[tuple[str, str]]]] = []
    unplaced = list(netids)

    while unplaced:
        seed = unplaced.pop(0)
        group_netids = [seed]
        common = set(schedules.get(seed, set()))

        while len(group_netids) < max_group_size and unplaced:
            best_candidate = None
            best_intersection_size = -1
            for cand in unplaced:
                inter = common & schedules.get(cand, set())
                if len(inter) > best_intersection_size:
                    best_intersection_size = len(inter)
                    best_candidate = cand
            if best_candidate is None:
                break
            group_netids.append(best_candidate)
            common = common & schedules.get(best_candidate, set())
            unplaced.remove(best_candidate)

        if min_group_size <= len(group_netids) <= max_group_size:
            remainder_groups.append((group_netids, common))
        else:
            unplaced.extend(group_netids)

    return remainder_groups, unplaced


def format_common_slots(common: set[tuple[str, str]]) -> list[str]:
# Formatting
    by_day: dict[str, list[str]] = {}
    for day, slot in sorted(common, key=lambda x: (WEEKDAYS.index(x[0]) if x[0] in WEEKDAYS else 99, x[1])):
        by_day.setdefault(day, []).append(slot)
    return [f"{day}: {', '.join(sorted(by_day[day]))}" for day in WEEKDAYS if day in by_day]


def build_export_df(
    groups: list[tuple[list[str], set[tuple[str, str]]]],
    manual_review: list[str],
    remainder_groups: list[tuple[list[str], set[tuple[str, str]]]] | None = None,
) -> pd.DataFrame:
# Export FM
    rows = []
    for i, (members, common) in enumerate(groups, start=1):
        common_str = "; ".join(format_common_slots(common))
        for netid in members:
            rows.append({
                "Group": i,
                "NetID": netid,
                "In_Group": "Yes",
                "Common_Meeting_Times": common_str,
                "Manual_Review": "",
            })
    if remainder_groups:
        for i, (members, common) in enumerate(remainder_groups, start=1):
            common_str = "; ".join(format_common_slots(common))
            for netid in members:
                rows.append({
                    "Group": f"Remainder {i}",
                    "NetID": netid,
                    "In_Group": "Yes (remainder)",
                    "Common_Meeting_Times": common_str,
                    "Manual_Review": "",
                })
    for netid in manual_review:
        rows.append({
            "Group": "",
            "NetID": netid,
            "In_Group": "No",
            "Common_Meeting_Times": "",
            "Manual_Review": "Yes",
        })
    return pd.DataFrame(rows)


def run_app():
    st.set_page_config(page_title="Student Group Matchmaking", layout="wide")
    st.title("Student Group Matchmaking")

    uploaded = st.file_uploader("Upload Form Responses CSV", type=["csv"])

    if uploaded is not None:
        try:
            df = pd.read_csv(uploaded)
            st.session_state["form_csv_df"] = df
        except Exception as e:
            st.error(f"Could not read CSV: {e}")
            return
    if "form_csv_df" not in st.session_state:
        st.info("Upload a CSV file to begin.")
        return
    df = st.session_state["form_csv_df"]

    netid_col = find_netid_column(df)
    if netid_col is None:
        st.error("No column containing 'NetID' found in the CSV. Please ensure the form has a NetID question.")
        return

    day_cols = find_day_columns(df)
    if len(day_cols) < 7:
        st.warning(f"Found {len(day_cols)} day columns (expected 7). Columns used: {day_cols}")

    col1, col2, col3 = st.columns(3)
    with col1:
        min_group_size = st.number_input(
            "Min group size",
            min_value=1,
            max_value=10,
            value=3,
            step=1,
            help="Minimum number of members per group (e.g. 3 for 3–4).",
        )
    with col2:
        max_group_size = st.number_input(
            "Max group size",
            min_value=1,
            max_value=10,
            value=4,
            step=1,
            help="Maximum number of members per group (e.g. 4 for 3–4).",
        )
    with col3:
        min_common = st.number_input(
            "Minimum common time slots (hours)",
            min_value=1,
            max_value=10,
            value=1,
            step=1,
            help="At least this many identical (day, time) slots required.",
        )

    if min_group_size > max_group_size:
        st.error("Min group size must be ≤ max group size.")
    elif st.button("Build groups"):
        schedules = build_master_schedule(df, netid_col, day_cols)
        if not schedules:
            st.warning("No valid NetIDs/schedules found after cleaning.")
            return

        groups, manual_review = greedy_group(
            schedules, min_group_size, max_group_size, min_common_slots=min_common
        )
        st.session_state["groups"] = groups
        st.session_state["manual_review"] = manual_review
        st.session_state["remainder_pool"] = list(manual_review)  # fixed pool for remainder scenarios
        st.session_state["schedules"] = schedules
        st.session_state["remainder_groups"] = []
        st.session_state["remainder_still_unplaced"] = []
        st.session_state["remainder_run_done"] = False

    if "groups" not in st.session_state:
        return

    groups = st.session_state["groups"]
    manual_review = st.session_state["manual_review"]

    st.subheader("Groups")
    for i, (members, common) in enumerate(groups, start=1):
        with st.expander(f"Group {i}: {', '.join(members)}", expanded=True):
            st.markdown("**Members:** " + ", ".join(members))
            if common:
                st.markdown("**Common meeting times (exact match):**")
                for line in format_common_slots(common):
                    st.markdown(f"- {line}")
            else:
                st.markdown("*No common slots.*")

    if manual_review:
        st.subheader("Manual review")
        st.markdown("These students could not be placed in a group with the required overlap.")
        st.write(", ".join(manual_review))

    st.subheader("Export")
    remainder_groups = st.session_state.get("remainder_groups", [])
    export_manual_review = (
        st.session_state.get("remainder_still_unplaced", manual_review)
        if remainder_groups else manual_review
    )
    export_df = build_export_df(groups, export_manual_review, remainder_groups=remainder_groups or None)
    buf = io.StringIO()
    export_df.to_csv(buf, index=False)
    st.download_button(
        "Download Final_Groups.csv",
        data=buf.getvalue(),
        file_name="Final_Groups.csv",
        mime="text/csv",
    )

# Try and matchmake remainder of students of best
    st.divider()
    st.subheader("Matchmake remainder students")
    st.markdown("Try different **min/max group sizes** on the same remainder pool")

    remainder_pool = st.session_state.get("remainder_pool", [])
    remainder_groups = st.session_state.get("remainder_groups", [])
    remainder_still_unplaced = st.session_state.get("remainder_still_unplaced", [])
    has_remainder_pool = bool(remainder_pool)
    has_remainder_results = bool(remainder_groups)

    if not has_remainder_pool and not has_remainder_results:
        st.info(
            "No remainder students right now — either everyone was placed in groups above, or you haven’t run **Build groups** yet. "
            "Run **Build groups** with different min/max or min common slots; anyone who can’t be placed will appear here."
        )
    else:
        st.markdown("**Remainder pool (same list for every run):** " + ", ".join(remainder_pool))

        if "remainder_groups" not in st.session_state:
            st.session_state["remainder_groups"] = []
        rem_min = st.number_input(
            "Remainder min group size",
            min_value=1,
            max_value=10,
            value=2,
            step=1,
            key="rem_min",
            help="e.g. 2 for 2–4, or 1 for 1–3.",
        )
        rem_max = st.number_input(
            "Remainder max group size",
            min_value=1,
            max_value=10,
            value=4,
            step=1,
            key="rem_max",
            help="e.g. 4 for 2–4, or 3 for 1–3.",
        )
        if rem_min > rem_max:
            st.error("Remainder min must be ≤ remainder max.")
        elif st.button("Run remainder matchmaking", key="run_remainder"):
            schedules = st.session_state.get("schedules", {})
            if not schedules:
                st.warning("No schedules in session. Run \"Build groups\" first.")
            else:
                new_remainder_groups, still_unplaced = greedy_group_remainder(
                    schedules, list(remainder_pool), rem_min, rem_max
                )
                st.session_state["remainder_groups"] = new_remainder_groups
                st.session_state["remainder_still_unplaced"] = still_unplaced
                st.session_state["remainder_run_done"] = True
                st.rerun()

# Results for remainder 
        if has_remainder_results:
            st.success(f"Matchmaking complete. **{len(remainder_groups)}** remainder group(s) formed (min–max **{rem_min}–{rem_max}**). Change the numbers above and run again to try another scenario.")
            st.markdown("**Remainder groups (best-effort):**")
            for i, (members, common) in enumerate(remainder_groups, start=1):
                with st.expander(f"Remainder group {i}: {', '.join(members)}", expanded=True):
                    st.markdown("**Members:** " + ", ".join(members))
                    if common:
                        st.markdown("**Common meeting times:**")
                        for line in format_common_slots(common):
                            st.markdown(f"- {line}")
                    else:
                        st.markdown("*No common slots (best-effort placement).*")
            if remainder_still_unplaced:
                st.markdown("**Still unplaced:** " + ", ".join(remainder_still_unplaced))
        elif st.session_state.get("remainder_run_done") and has_remainder_pool:
            st.warning("No groups formed with the current min–max. Try different values (e.g. 1–4) and run again.")


if __name__ == "__main__":
    run_app()
