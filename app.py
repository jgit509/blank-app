"""
app.py — Land Vetting & Task Tracker
Streamlit application with nested task hierarchy.

Run with: streamlit run app.py
"""

import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
import database as db

# ── Initialize ─────────────────────────────────────────────
db.init_db()

# ── Page Config ────────────────────────────────────────────
st.set_page_config(
    page_title="🏗️ Land Tracker",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Constants ──────────────────────────────────────────────
STATUS_OPTIONS = [
    "New Lead", "Researching", "Contacted Owner", "Offer Made",
    "Negotiating", "Under Contract", "Due Diligence",
    "Closed", "Passed", "Dead Deal"
]

PRIORITY_OPTIONS = ["Hot Deal", "Warm", "Cold"]

TASK_PRIORITY_OPTIONS = ["High", "Medium", "Low"]

STATUS_COLORS = {
    "New Lead": "#fff2cc",
    "Researching": "#d0e0e3",
    "Contacted Owner": "#fce5cd",
    "Offer Made": "#d9d2e9",
    "Negotiating": "#c9daf8",
    "Under Contract": "#b7e1cd",
    "Due Diligence": "#cfe2f3",
    "Closed": "#57bb8a",
    "Passed": "#d9d9d9",
    "Dead Deal": "#f4c7c3",
}

PRIORITY_COLORS = {
    "Hot Deal": "#ea4335",
    "Warm": "#fbbc04",
    "Cold": "#e8eaed",
}

TASK_PRIORITY_COLORS = {
    "High": "#ea4335",
    "Medium": "#fbbc04",
    "Low": "#e8eaed",
}


# ── Helper Functions ───────────────────────────────────────

def priority_badge(priority: str, task_level: bool = False) -> str:
    """Return an HTML badge for priority."""
    colors = TASK_PRIORITY_COLORS if task_level else PRIORITY_COLORS
    color = colors.get(priority, "#e8eaed")
    text_color = "#fff" if priority in ["Hot Deal", "High"] else "#333"
    return (
        f'<span style="background:{color};color:{text_color};'
        f'padding:2px 10px;border-radius:12px;font-size:0.8em;'
        f'font-weight:600;">{priority}</span>'
    )


def status_badge(status: str) -> str:
    """Return an HTML badge for status."""
    color = STATUS_COLORS.get(status, "#e8eaed")
    text_color = "#fff" if status in ["Closed", "Dead Deal"] else "#333"
    return (
        f'<span style="background:{color};color:{text_color};'
        f'padding:2px 10px;border-radius:12px;font-size:0.8em;'
        f'font-weight:600;">{status}</span>'
    )


def format_date(d) -> str:
    """Format a date/datetime string for display."""
    if not d or d == "":
        return "—"
    try:
        if isinstance(d, str):
            if "T" in d or " " in d:
                dt = datetime.fromisoformat(d.replace("Z", ""))
                return dt.strftime("%b %d, %Y %I:%M %p")
            else:
                dt = datetime.strptime(d, "%Y-%m-%d")
                return dt.strftime("%b %d, %Y")
        return str(d)
    except Exception:
        return str(d)


# ── Sidebar Navigation ────────────────────────────────────

st.sidebar.title("🏗️ Land Tracker")
st.sidebar.markdown("---")

page = st.sidebar.radio(
    "Navigate",
    [
        "📊 Dashboard",
        "🏗️ Properties",
        "📋 Task Board",
        "👥 Team",
    ],
    label_visibility="collapsed",
)

st.sidebar.markdown("---")
st.sidebar.caption(f"Last loaded: {datetime.now().strftime('%b %d, %I:%M %p')}")


# ================================================================
# 📊 DASHBOARD PAGE
# ================================================================

if page == "📊 Dashboard":
    st.title("📊 Dashboard")
    st.markdown("Your land portfolio at a glance.")
    st.markdown("---")

    stats = db.get_stats()

    # ── Top Metrics ────────────────────────────────────────
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Properties", stats["total_properties"])
    col2.metric("Open Tasks", stats["open_tasks"])
    col3.metric("Completed Tasks", stats["done_tasks"])
    col4.metric("⚠️ Overdue", stats["overdue_tasks"])

    st.markdown("---")

    # ── Status Breakdown ───────────────────────────────────
    left, right = st.columns(2)

    with left:
        st.subheader("Properties by Status")
        if stats["by_status"]:
            for item in stats["by_status"]:
                badge = status_badge(item["status"])
                st.markdown(
                    f'{badge} &nbsp; **{item["count"]}** properties',
                    unsafe_allow_html=True,
                )
        else:
            st.info("No properties yet. Add some on the Properties page!")

    with right:
        st.subheader("Properties by Priority")
        if stats["by_priority"]:
            for item in stats["by_priority"]:
                badge = priority_badge(item["priority"])
                st.markdown(
                    f'{badge} &nbsp; **{item["count"]}** properties',
                    unsafe_allow_html=True,
                )
        else:
            st.info("No properties yet.")

    st.markdown("---")

    # ── Tasks by Assignee ──────────────────────────────────
    st.subheader("Open Tasks by Assignee")
    if stats["by_assignee"]:
        assignee_cols = st.columns(min(len(stats["by_assignee"]), 4))
        for i, item in enumerate(stats["by_assignee"]):
            col_idx = i % len(assignee_cols)
            assignee_cols[col_idx].metric(
                item["assigned_to"] or "Unassigned",
                f'{item["count"]} tasks'
            )
    else:
        st.info("No open tasks assigned yet.")

    st.markdown("---")

    # ── Upcoming Tasks Preview ─────────────────────────────
    st.subheader("⏰ Upcoming Tasks (Next 7 Days)")
    upcoming = db.get_upcoming_tasks(7)
    if upcoming:
        for task in upcoming[:10]:
            done_icon = "✅" if task["done"] else "⬜"
            due = format_date(task.get("due_date"))
            pri_badge = priority_badge(task["priority"], task_level=True)
            assigned = task["assigned_to"] or "Unassigned"
            st.markdown(
                f'{done_icon} **{task["property_address"]}** → '
                f'{task["description"]} &nbsp; {pri_badge} &nbsp; '
                f'👤 {assigned} &nbsp; 📅 {due}',
                unsafe_allow_html=True,
            )
    else:
        st.success("No upcoming deadlines. You're clear! 🎉")


# ================================================================
# 🏗️ PROPERTIES PAGE
# ================================================================

elif page == "🏗️ Properties":
    st.title("🏗️ Properties")
    st.markdown("Manage your land parcels. Each property has nested subtasks.")
    st.markdown("---")

    # ── Add New Property ───────────────────────────────────
    with st.expander("➕ Add New Property", expanded=False):
        with st.form("add_property_form", clear_on_submit=True):
            ap_col1, ap_col2 = st.columns(2)
            with ap_col1:
                new_address = st.text_input(
                    "Property Address *",
                    placeholder="123 Main St, Austin TX 78701"
                )
                new_url = st.text_input(
                    "URL",
                    placeholder="https://zillow.com/..."
                )
            with ap_col2:
                new_status = st.selectbox("Status", STATUS_OPTIONS)
                new_priority = st.selectbox("Priority", PRIORITY_OPTIONS)

            new_notes = st.text_area(
                "Notes",
                placeholder="Due diligence notes, research, observations...",
                height=100,
            )
            new_action = st.text_input(
                "Action Item",
                placeholder="Next step for this property"
            )

            submitted = st.form_submit_button(
                "Add Property", use_container_width=True, type="primary"
            )
            if submitted:
                if new_address.strip():
                    db.add_property(
                        address=new_address.strip(),
                        url=new_url.strip(),
                        notes=new_notes.strip(),
                        action_item=new_action.strip(),
                        status=new_status,
                        priority=new_priority,
                    )
                    st.success(f"Added: {new_address}")
                    st.rerun()
                else:
                    st.error("Property address is required.")

    # ── Filters ────────────────────────────────────────────
    filter_col1, filter_col2, filter_col3 = st.columns(3)
    with filter_col1:
        filter_status = st.multiselect(
            "Filter by Status",
            STATUS_OPTIONS,
            default=[],
            placeholder="All statuses",
        )
    with filter_col2:
        filter_priority = st.multiselect(
            "Filter by Priority",
            PRIORITY_OPTIONS,
            default=[],
            placeholder="All priorities",
        )
    with filter_col3:
        search_term = st.text_input(
            "🔍 Search",
            placeholder="Search address, notes..."
        )

    st.markdown("---")

    # ── Property List with Nested Subtasks ─────────────────
    properties = db.get_all_properties()

    # Apply filters
    if filter_status:
        properties = [p for p in properties if p["status"] in filter_status]
    if filter_priority:
        properties = [p for p in properties if p["priority"] in filter_priority]
    if search_term:
        term = search_term.lower()
        properties = [
            p for p in properties
            if term in (p["address"] or "").lower()
            or term in (p["notes"] or "").lower()
            or term in (p["url"] or "").lower()
            or term in (p["action_item"] or "").lower()
        ]

    if not properties:
        st.info("No properties found. Add one above! ☝️")
    else:
        st.caption(f"Showing {len(properties)} properties")

    for prop in properties:
        subtasks = db.get_subtasks(prop["id"])
        open_count = sum(1 for t in subtasks if not t["done"])
        done_count = sum(1 for t in subtasks if t["done"])

        # ── Property Header ───────────────────────────────
        s_badge = status_badge(prop["status"])
        p_badge = priority_badge(prop["priority"])
        task_summary = f"📋 {open_count} open · {done_count} done"

        with st.expander(
            f'📍 {prop["address"]}  —  {prop["status"]}  |  '
            f'{prop["priority"]}  |  {task_summary}',
            expanded=False,
        ):
            # ── Property Details ───────────────────────────
            detail_col1, detail_col2 = st.columns([2, 1])

            with detail_col1:
                st.markdown(
                    f"**Status:** {s_badge} &nbsp;&nbsp; "
                    f"**Priority:** {p_badge}",
                    unsafe_allow_html=True,
                )
                if prop["url"]:
                    st.markdown(f"🔗 [View Listing]({prop['url']})")
                if prop["action_item"]:
                    st.markdown(f"🎯 **Action Item:** {prop['action_item']}")
                if prop["notes"]:
                    st.markdown(f"📝 **Notes:** {prop['notes']}")
                st.caption(f"Added: {format_date(prop['date_added'])}")

            with detail_col2:
                st.metric("Open Tasks", open_count)
                st.metric("Completed", done_count)

            # ── Edit Property ──────────────────────────────
            with st.popover("✏️ Edit Property"):
                with st.form(f"edit_prop_{prop['id']}"):
                    edit_address = st.text_input(
                        "Address", value=prop["address"],
                        key=f"ea_{prop['id']}"
                    )
                    edit_url = st.text_input(
                        "URL", value=prop["url"] or "",
                        key=f"eu_{prop['id']}"
                    )
                    edit_notes = st.text_area(
                        "Notes", value=prop["notes"] or "",
                        key=f"en_{prop['id']}", height=80
                    )
                    edit_action = st.text_input(
                        "Action Item", value=prop["action_item"] or "",
                        key=f"eai_{prop['id']}"
                    )
                    edit_status = st.selectbox(
                        "Status", STATUS_OPTIONS,
                        index=STATUS_OPTIONS.index(prop["status"])
                            if prop["status"] in STATUS_OPTIONS else 0,
                        key=f"es_{prop['id']}"
                    )
                    edit_priority = st.selectbox(
                        "Priority", PRIORITY_OPTIONS,
                        index=PRIORITY_OPTIONS.index(prop["priority"])
                            if prop["priority"] in PRIORITY_OPTIONS else 1,
                        key=f"ep_{prop['id']}"
                    )

                    ec1, ec2 = st.columns(2)
                    with ec1:
                        if st.form_submit_button(
                            "Save", use_container_width=True, type="primary"
                        ):
                            db.update_property(
                                prop["id"],
                                address=edit_address,
                                url=edit_url,
                                notes=edit_notes,
                                action_item=edit_action,
                                status=edit_status,
                                priority=edit_priority,
                            )
                            st.rerun()
                    with ec2:
                        if st.form_submit_button(
                            "🗑️ Delete", use_container_width=True
                        ):
                            db.delete_property(prop["id"])
                            st.rerun()

            st.markdown("---")

            # ── Subtasks Section ───────────────────────────
            st.markdown("##### 📋 Subtasks")

            # Add subtask form
            team_names = db.get_team_names()
            assign_options = [""] + team_names

            with st.form(f"add_subtask_{prop['id']}", clear_on_submit=True):
                st_col1, st_col2, st_col3, st_col4 = st.columns([3, 1, 1, 1])
                with st_col1:
                    new_task_desc = st.text_input(
                        "Task", placeholder="What needs to be done?",
                        key=f"ntd_{prop['id']}", label_visibility="collapsed"
                    )
                with st_col2:
                    new_task_assigned = st.selectbox(
                        "Assign", assign_options,
                        key=f"nta_{prop['id']}", label_visibility="collapsed"
                    )
                with st_col3:
                    new_task_priority = st.selectbox(
                        "Priority", TASK_PRIORITY_OPTIONS,
                        index=1, key=f"ntp_{prop['id']}",
                        label_visibility="collapsed"
                    )
                with st_col4:
                    new_task_due = st.date_input(
                        "Due", value=None,
                        key=f"ntdu_{prop['id']}",
                        label_visibility="collapsed"
                    )

                if st.form_submit_button(
                    "➕ Add Subtask", use_container_width=True
                ):
                    if new_task_desc.strip():
                        due_str = (
                            new_task_due.isoformat()
                            if new_task_due else None
                        )
                        db.add_subtask(
                            property_id=prop["id"],
                            description=new_task_desc.strip(),
                            assigned_to=new_task_assigned,
                            priority=new_task_priority,
                            due_date=due_str,
                        )
                        st.rerun()
                    else:
                        st.error("Task description required.")

            # Display subtasks
            if subtasks:
                for task in subtasks:
                    t_col1, t_col2, t_col3, t_col4, t_col5, t_col6 = (
                        st.columns([0.5, 3, 1, 1, 1, 0.5])
                    )

                    with t_col1:
                        is_done = st.checkbox(
                            "Done",
                            value=bool(task["done"]),
                            key=f"cb_{task['id']}",
                            label_visibility="collapsed",
                        )
                        if is_done != bool(task["done"]):
                            db.toggle_subtask(task["id"])
                            st.rerun()

                    with t_col2:
                        desc_style = (
                            "text-decoration: line-through; color: #999;"
                            if task["done"] else ""
                        )
                        st.markdown(
                            f'<span style="{desc_style}">'
                            f'{task["description"]}</span>',
                            unsafe_allow_html=True,
                        )

                    with t_col3:
                        st.markdown(
                            priority_badge(task["priority"], task_level=True),
                            unsafe_allow_html=True,
                        )

                    with t_col4:
                        assigned = task["assigned_to"] or "—"
                        st.caption(f"👤 {assigned}")

                    with t_col5:
                        due = format_date(task.get("due_date"))
                        if (
                            task.get("due_date")
                            and not task["done"]
                            and task["due_date"] < date.today().isoformat()
                        ):
                            st.markdown(
                                f'<span style="color:#ea4335;font-weight:600;">'
                                f'⚠️ {due}</span>',
                                unsafe_allow_html=True,
                            )
                        else:
                            st.caption(f"📅 {due}")

                    with t_col6:
                        if st.button(
                            "🗑️", key=f"del_task_{task['id']}",
                            help="Delete this subtask"
                        ):
                            db.delete_subtask(task["id"])
                            st.rerun()
            else:
                st.caption("No subtasks yet. Add one above.")

            st.markdown("---")

            # ── Conversation Log ───────────────────────────
            st.markdown("##### 💬 Conversation Log")

            with st.form(
                f"add_log_{prop['id']}", clear_on_submit=True
            ):
                log_msg = st.text_area(
                    "Add update",
                    placeholder=(
                        "Type your update...\n\n"
                        "Tip: Start a line with ACTION: to auto-create a subtask"
                    ),
                    key=f"log_{prop['id']}",
                    height=80,
                    label_visibility="collapsed",
                )
                log_col1, log_col2 = st.columns([3, 1])
                with log_col2:
                    log_author = st.selectbox(
                        "As", assign_options if assign_options else ["Owner"],
                        key=f"la_{prop['id']}",
                        label_visibility="collapsed",
                    )
                if st.form_submit_button(
                    "💬 Add to Log", use_container_width=True
                ):
                    if log_msg.strip():
                        author = log_author if log_author else "Owner"
                        lines = log_msg.strip().split("\n")
                        message_lines = []
                        actions = []

                        for line in lines:
                            stripped = line.strip()
                            if stripped.upper().startswith("ACTION:"):
                                action_text = stripped[7:].strip()
                                if action_text:
                                    actions.append(action_text)
                                    message_lines.append(
                                        f">> NEW TASK: {action_text}"
                                    )
                            else:
                                message_lines.append(stripped)

                        full_message = "\n".join(message_lines)
                        db.add_log_entry(
                            prop["id"], full_message, author
                        )

                        # Auto-create subtasks from ACTION: lines
                        for action in actions:
                            db.add_subtask(
                                property_id=prop["id"],
                                description=action,
                                assigned_to=log_author or "",
                                priority="Medium",
                                created_by=author,
                            )

                        if actions:
                            # Update the property's action item
                            db.update_property(
                                prop["id"],
                                action_item=actions[-1]
                            )

                        st.rerun()

            # Display log entries
            log_entries = db.get_log_entries(prop["id"])
            if log_entries:
                for entry in log_entries:
                    ts = format_date(entry["timestamp"])
                    st.markdown(
                        f'<div style="background:#f8f9fa;padding:8px 12px;'
                        f'border-radius:8px;margin-bottom:6px;'
                        f'border-left:3px solid #1a73e8;">'
                        f'<strong>{entry["author"]}</strong> '
                        f'<span style="color:#888;font-size:0.85em;">'
                        f'— {ts}</span><br/>'
                        f'{entry["message"].replace(chr(10), "<br/>")}'
                        f'</div>',
                        unsafe_allow_html=True,
                    )
            else:
                st.caption("No log entries yet.")


# ================================================================
# 📋 TASK BOARD PAGE
# ================================================================

elif page == "📋 Task Board":
    st.title("📋 Task Board")
    st.markdown("All tasks across all properties, organized by status.")
    st.markdown("---")

    # ── Tab Layout ─────────────────────────────────────────
    tab_upcoming, tab_all_open, tab_completed, tab_overdue = st.tabs(
        ["⏰ Upcoming", "📂 All Open", "✅ Completed", "⚠️ Overdue"]
    )

    # ── Upcoming Tab ───────────────────────────────────────
    with tab_upcoming:
        days_ahead = st.slider(
            "Show tasks due within:", 1, 30, 7,
            format="%d days"
        )
        upcoming = db.get_upcoming_tasks(days_ahead)

        if upcoming:
            st.caption(
                f"{len(upcoming)} tasks due in the next {days_ahead} days"
            )

            # Group by property
            grouped = {}
            for task in upcoming:
                addr = task["property_address"]
                if addr not in grouped:
                    grouped[addr] = []
                grouped[addr].append(task)

            for address, tasks in grouped.items():
                st.markdown(
                    f'<div style="background:#e8eaed;padding:6px 12px;'
                    f'border-radius:6px;margin:12px 0 4px 0;'
                    f'font-weight:700;color:#1a73e8;">'
                    f'📍 {address} ({len(tasks)} tasks)</div>',
                    unsafe_allow_html=True,
                )

                for task in tasks:
                    tc1, tc2, tc3, tc4, tc5 = st.columns(
                        [0.5, 3, 1, 1, 1]
                    )
                    with tc1:
                        done = st.checkbox(
                            "d", value=bool(task["done"]),
                            key=f"up_{task['id']}",
                            label_visibility="collapsed",
                        )
                        if done != bool(task["done"]):
                            db.toggle_subtask(task["id"])
                            st.rerun()
                    with tc2:
                        st.write(task["description"])
                    with tc3:
                        st.markdown(
                            priority_badge(
                                task["priority"], task_level=True
                            ),
                            unsafe_allow_html=True,
                        )
                    with tc4:
                        st.caption(
                            f'👤 {task["assigned_to"] or "Unassigned"}'
                        )
                    with tc5:
                        due_str = format_date(task.get("due_date"))
                        is_overdue = (
                            task.get("due_date")
                            and task["due_date"] < date.today().isoformat()
                        )
                        if is_overdue:
                            st.markdown(
                                f'<span style="color:#ea4335;'
                                f'font-weight:600;">⚠️ {due_str}</span>',
                                unsafe_allow_html=True,
                            )
                        else:
                            st.caption(f"📅 {due_str}")
        else:
            st.success(
                f"No tasks due in the next {days_ahead} days. "
                f"You're ahead of schedule! 🎉"
            )

    # ── All Open Tab ───────────────────────────────────────
    with tab_all_open:
        all_tasks = db.get_all_subtasks()
        open_tasks = [t for t in all_tasks if not t["done"]]

        if open_tasks:
            # Filter options
            ft_col1, ft_col2 = st.columns(2)
            with ft_col1:
                filter_assignee = st.multiselect(
                    "Filter by Assignee",
                    list(set(
                        t["assigned_to"] for t in open_tasks
                        if t["assigned_to"]
                    )),
                    placeholder="All assignees",
                    key="filter_assignee_open",
                )
            with ft_col2:
                filter_task_priority = st.multiselect(
                    "Filter by Priority",
                    TASK_PRIORITY_OPTIONS,
                    placeholder="All priorities",
                    key="filter_priority_open",
                )

            filtered = open_tasks
            if filter_assignee:
                filtered = [
                    t for t in filtered
                    if t["assigned_to"] in filter_assignee
                ]
            if filter_task_priority:
                filtered = [
                    t for t in filtered
                    if t["priority"] in filter_task_priority
                ]

            st.caption(f"{len(filtered)} open tasks")

            # Group by property
            grouped = {}
            for task in filtered:
                addr = task["property_address"]
                if addr not in grouped:
                    grouped[addr] = []
                grouped[addr].append(task)

            for address, tasks in grouped.items():
                st.markdown(
                    f'<div style="background:#e8eaed;padding:6px 12px;'
                    f'border-radius:6px;margin:12px 0 4px 0;'
                    f'font-weight:700;color:#1a73e8;">'
                    f'📍 {address} ({len(tasks)} tasks)</div>',
                    unsafe_allow_html=True,
                )

                for task in tasks:
                    tc1, tc2, tc3, tc4, tc5 = st.columns(
                        [0.5, 3, 1, 1, 1]
                    )
                    with tc1:
                        done = st.checkbox(
                            "d", value=False,
                            key=f"ao_{task['id']}",
                            label_visibility="collapsed",
                        )
                        if done:
                            db.toggle_subtask(task["id"])
                            st.rerun()
                    with tc2:
                        st.write(task["description"])
                    with tc3:
                        st.markdown(
                            priority_badge(
                                task["priority"], task_level=True
                            ),
                            unsafe_allow_html=True,
                        )
                    with tc4:
                        st.caption(
                            f'👤 {task["assigned_to"] or "Unassigned"}'
                        )
                    with tc5:
                        st.caption(
                            f'📅 {format_date(task.get("due_date"))}'
                        )
        else:
            st.success("All tasks completed! 🎉")

    # ── Completed Tab ──────────────────────────────────────
    with tab_completed:
        completed = db.get_completed_tasks(50)

        if completed:
            st.caption(f"Showing last {len(completed)} completed tasks")

            # Group by property
            grouped = {}
            for task in completed:
                addr = task["property_address"]
                if addr not in grouped:
                    grouped[addr] = []
                grouped[addr].append(task)

            for address, tasks in grouped.items():
                st.markdown(
                    f'<div style="background:#f1f8e9;padding:6px 12px;'
                    f'border-radius:6px;margin:12px 0 4px 0;'
                    f'font-weight:700;color:#2e7d32;">'
                    f'✅ {address} ({len(tasks)} completed)</div>',
                    unsafe_allow_html=True,
                )

                for task in tasks:
                    tc1, tc2, tc3, tc4 = st.columns([0.5, 3, 1, 1.5])
                    with tc1:
                        st.checkbox(
                            "d", value=True,
                            key=f"ct_{task['id']}",
                            label_visibility="collapsed",
                            disabled=True,
                        )
                    with tc2:
                        st.markdown(
                            f'<span style="text-decoration:line-through;'
                            f'color:#999;">{task["description"]}</span>',
                            unsafe_allow_html=True,
                        )
                    with tc3:
                        st.caption(
                            f'👤 {task["assigned_to"] or "—"}'
                        )
                    with tc4:
                        st.caption(
                            f'Done: {format_date(task.get("completed_date"))}'
                        )
        else:
            st.info("No completed tasks yet.")

    # ── Overdue Tab ────────────────────────────────────────
    with tab_overdue:
        all_tasks = db.get_all_subtasks()
        today_str = date.today().isoformat()
        overdue = [
            t for t in all_tasks
            if not t["done"]
            and t.get("due_date")
            and t["due_date"] != ""
            and t["due_date"] < today_str
        ]

        if overdue:
            st.error(f"⚠️ {len(overdue)} overdue tasks need attention!")

            for task in overdue:
                tc1, tc2, tc3, tc4, tc5 = st.columns(
                    [0.5, 2.5, 1, 1, 1]
                )
                with tc1:
                    done = st.checkbox(
                        "d", value=False,
                        key=f"od_{task['id']}",
                        label_visibility="collapsed",
                    )
                    if done:
                        db.toggle_subtask(task["id"])
                        st.rerun()
                with tc2:
                    st.markdown(
                        f'**{task["property_address"]}**<br/>'
                        f'{task["description"]}',
                        unsafe_allow_html=True,
                    )
                with tc3:
                    st.markdown(
                        priority_badge(task["priority"], task_level=True),
                        unsafe_allow_html=True,
                    )
                with tc4:
                    st.caption(
                        f'👤 {task["assigned_to"] or "Unassigned"}'
                    )
                with tc5:
                    st.markdown(
                        f'<span style="color:#ea4335;font-weight:600;">'
                        f'📅 {format_date(task.get("due_date"))}</span>',
                        unsafe_allow_html=True,
                    )
        else:
            st.success("No overdue tasks! 🎉")


# ================================================================
# 👥 TEAM PAGE
# ================================================================

elif page == "👥 Team":
    st.title("👥 Team")
    st.markdown("Manage team members who can be assigned to tasks.")
    st.markdown("---")

    # ── Add Team Member ────────────────────────────────────
    with st.form("add_team_form", clear_on_submit=True):
        tm_col1, tm_col2, tm_col3 = st.columns(3)
        with tm_col1:
            new_name = st.text_input("Name *", placeholder="John Smith")
        with tm_col2:
            new_email = st.text_input(
                "Email", placeholder="john@example.com"
            )
        with tm_col3:
            new_role = st.selectbox(
                "Role", ["Owner", "Team Member", "Contractor", "Agent"]
            )

        if st.form_submit_button(
            "➕ Add Team Member", use_container_width=True, type="primary"
        ):
            if new_name.strip():
                db.add_team_member(
                    new_name.strip(), new_email.strip(), new_role
                )
                st.success(f"Added {new_name}")
                st.rerun()
            else:
                st.error("Name is required.")

    st.markdown("---")

    # ── Team List ──────────────────────────────────────────
    members = db.get_team_members()

    if members:
        for member in members:
            m_col1, m_col2, m_col3, m_col4 = st.columns([2, 3, 1.5, 0.5])
            with m_col1:
                st.markdown(f"**{member['name']}**")
            with m_col2:
                st.caption(member["email"] or "No email")
            with m_col3:
                st.caption(f"🏷️ {member['role']}")
            with m_col4:
                if st.button(
                    "🗑️", key=f"del_tm_{member['id']}",
                    help="Remove team member"
                ):
                    db.delete_team_member(member["id"])
                    st.rerun()

        # ── Workload Overview ──────────────────────────────
        st.markdown("---")
        st.subheader("📊 Workload Overview")

        all_tasks = db.get_all_subtasks()
        for member in members:
            member_tasks = [
                t for t in all_tasks
                if t["assigned_to"] == member["name"]
            ]
            open_t = sum(1 for t in member_tasks if not t["done"])
            done_t = sum(1 for t in member_tasks if t["done"])
            total = open_t + done_t

            if total > 0:
                progress = done_t / total
                st.markdown(f"**{member['name']}** — {open_t} open, {done_t} done")
                st.progress(progress)
            else:
                st.markdown(f"**{member['name']}** — No tasks assigned")
                st.progress(0.0)
    else:
        st.info(
            "No team members yet. Add yourself and your team above! ☝️"
        )
