from __future__ import annotations

import csv
import io
import json
import uuid
from datetime import date, datetime
from pathlib import Path
from typing import Any

import streamlit as st


DATA_FILE = Path(__file__).with_name("tasks.json")

STATUS_OPTIONS = ["Open", "In Progress", "Done"]
PRIORITY_OPTIONS = ["High", "Normal", "Low"]
STATUS_RANK = {name: index for index, name in enumerate(STATUS_OPTIONS)}
PRIORITY_RANK = {"High": 0, "Normal": 1, "Low": 2}


def set_page_style() -> None:
    st.set_page_config(page_title="Focus Board", layout="wide")
    st.markdown(
        """
        <style>
        :root {
          --bg: #eef2f6;
          --panel: #ffffff;
          --panel-soft: #f7f9fc;
          --ink: #141820;
          --muted: #5e6a78;
          --line: #d8e0ea;
          --accent: #155eef;
          --accent-2: #0f8b6f;
          --warn: #c27a18;
          --danger: #b03838;
        }

        .stApp {
          background:
            radial-gradient(circle at top right, rgba(21, 94, 239, 0.12), transparent 28%),
            radial-gradient(circle at bottom left, rgba(15, 139, 111, 0.10), transparent 30%),
            var(--bg);
          color: var(--ink);
        }

        .hero {
          padding: 1rem 1.25rem;
          border: 1px solid var(--line);
          border-radius: 12px;
          background: color-mix(in srgb, var(--panel) 92%, transparent);
          box-shadow: 0 18px 50px rgba(16, 24, 40, 0.08);
          margin-bottom: 1rem;
        }

        .hero h1 {
          margin: 0;
          font-size: 2.2rem;
          line-height: 1;
        }

        .hero p {
          margin: 0.35rem 0 0;
          color: var(--muted);
        }

        .metric {
          border: 1px solid var(--line);
          border-radius: 12px;
          padding: 0.9rem 1rem;
          background: var(--panel);
        }

        .metric .label {
          color: var(--muted);
          font-size: 0.8rem;
          text-transform: uppercase;
          letter-spacing: 0.04em;
          margin-bottom: 0.35rem;
        }

        .metric .value {
          font-size: 1.9rem;
          font-weight: 800;
          line-height: 1;
        }

        .task-card {
          border: 1px solid var(--line);
          border-radius: 12px;
          background: var(--panel);
          padding: 1rem;
          margin-bottom: 0.85rem;
        }

        .task-title {
          font-size: 1.08rem;
          font-weight: 800;
          margin: 0 0 0.3rem;
        }

        .task-title.done {
          color: var(--muted);
          text-decoration: line-through;
        }

        .task-meta {
          display: flex;
          flex-wrap: wrap;
          gap: 0.5rem;
          margin-top: 0.6rem;
        }

        .pill {
          display: inline-flex;
          align-items: center;
          min-height: 24px;
          padding: 0.15rem 0.55rem;
          border-radius: 999px;
          background: var(--panel-soft);
          color: var(--muted);
          font-size: 0.78rem;
          font-weight: 700;
        }

        .pill.high { color: var(--danger); }
        .pill.low { color: var(--accent-2); }
        .pill.warn { color: var(--warn); }
        .pill.done { color: var(--accent-2); }

        .subtle {
          color: var(--muted);
          font-size: 0.92rem;
        }

        div[data-testid="stSidebar"] {
          background: #f9fbfe;
          border-right: 1px solid var(--line);
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def now_stamp() -> str:
    return datetime.now().isoformat(timespec="seconds")


def default_tasks() -> list[dict[str, Any]]:
    stamp = now_stamp()
    return [
        {
            "id": str(uuid.uuid4()),
            "title": "Map out internship applications",
            "notes": "Track companies, deadlines, and follow-ups.",
            "status": "In Progress",
            "priority": "High",
            "due_date": date.today().isoformat(),
            "created_at": stamp,
            "updated_at": stamp,
        },
        {
            "id": str(uuid.uuid4()),
            "title": "Refine portfolio project summary",
            "notes": "Keep it specific and measurable.",
            "status": "Open",
            "priority": "Normal",
            "due_date": "",
            "created_at": stamp,
            "updated_at": stamp,
        },
    ]


def normalize_task(task: dict[str, Any]) -> dict[str, Any]:
    stamp = now_stamp()
    status = task.get("status") if task.get("status") in STATUS_OPTIONS else "Open"
    priority = task.get("priority") if task.get("priority") in PRIORITY_OPTIONS else "Normal"
    return {
        "id": str(task.get("id") or uuid.uuid4()),
        "title": str(task.get("title") or "").strip(),
        "notes": str(task.get("notes") or "").strip(),
        "status": status,
        "priority": priority,
        "due_date": str(task.get("due_date") or ""),
        "created_at": str(task.get("created_at") or stamp),
        "updated_at": str(task.get("updated_at") or stamp),
    }


def load_tasks() -> list[dict[str, Any]]:
    if not DATA_FILE.exists():
        return []
    try:
        raw = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    if not isinstance(raw, list):
        return []
    return [normalize_task(item) for item in raw if isinstance(item, dict)]


def save_tasks(tasks: list[dict[str, Any]]) -> None:
    try:
        DATA_FILE.write_text(json.dumps(tasks, indent=2), encoding="utf-8")
    except OSError:
        pass


def timestamp(value: str) -> float:
    try:
        return datetime.fromisoformat(value).timestamp()
    except ValueError:
        return 0.0


def due_timestamp(value: str) -> float:
    if not value:
        return float("inf")
    try:
        return datetime.combine(date.fromisoformat(value), datetime.min.time()).timestamp()
    except ValueError:
        return float("inf")


def ensure_state() -> None:
    defaults = {
        "tasks": load_tasks(),
        "editing_task_id": None,
        "search_query": "",
        "status_filter": "All",
        "sort_mode": "Newest",
        "form_title": "",
        "form_notes": "",
        "form_status": "Open",
        "form_priority": "Normal",
        "form_due_date": None,
    }
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)


def reset_form() -> None:
    st.session_state.editing_task_id = None
    st.session_state.form_title = ""
    st.session_state.form_notes = ""
    st.session_state.form_status = "Open"
    st.session_state.form_priority = "Normal"
    st.session_state.form_due_date = None


def set_editor(task_id: str) -> None:
    task = next((item for item in st.session_state.tasks if item["id"] == task_id), None)
    if not task:
        return
    st.session_state.editing_task_id = task_id
    st.session_state.form_title = task["title"]
    st.session_state.form_notes = task["notes"]
    st.session_state.form_status = task["status"]
    st.session_state.form_priority = task["priority"]
    st.session_state.form_due_date = date.fromisoformat(task["due_date"]) if task["due_date"] else None


def upsert_task() -> None:
    title = st.session_state.form_title.strip()
    if not title:
        st.error("Task title is required.")
        return

    due_value = st.session_state.form_due_date.isoformat() if st.session_state.form_due_date else ""
    stamp = now_stamp()

    if st.session_state.editing_task_id:
        updated = []
        for task in st.session_state.tasks:
            if task["id"] == st.session_state.editing_task_id:
                updated.append(
                    {
                        **task,
                        "title": title,
                        "notes": st.session_state.form_notes.strip(),
                        "status": st.session_state.form_status,
                        "priority": st.session_state.form_priority,
                        "due_date": due_value,
                        "updated_at": stamp,
                    }
                )
            else:
                updated.append(task)
        st.session_state.tasks = updated
    else:
        st.session_state.tasks.insert(
            0,
            {
                "id": str(uuid.uuid4()),
                "title": title,
                "notes": st.session_state.form_notes.strip(),
                "status": st.session_state.form_status,
                "priority": st.session_state.form_priority,
                "due_date": due_value,
                "created_at": stamp,
                "updated_at": stamp,
            },
        )

    save_tasks(st.session_state.tasks)
    reset_form()


def remove_task(task_id: str) -> None:
    st.session_state.tasks = [task for task in st.session_state.tasks if task["id"] != task_id]
    if st.session_state.editing_task_id == task_id:
        reset_form()
    save_tasks(st.session_state.tasks)


def set_status(task_id: str, status: str) -> None:
    updated = []
    stamp = now_stamp()
    for task in st.session_state.tasks:
        if task["id"] == task_id:
            updated.append({**task, "status": status, "updated_at": stamp})
        else:
            updated.append(task)
    st.session_state.tasks = updated
    save_tasks(st.session_state.tasks)


def load_samples() -> None:
    st.session_state.tasks = default_tasks() + st.session_state.tasks
    save_tasks(st.session_state.tasks)


def matches_filters(task: dict[str, Any]) -> bool:
    query = st.session_state.search_query.strip().lower()
    if query and query not in f"{task['title']} {task['notes']}".lower():
        return False

    if st.session_state.status_filter == "Open" and task["status"] == "Done":
        return False
    if st.session_state.status_filter == "Done" and task["status"] != "Done":
        return False
    return True


def sort_key(task: dict[str, Any]) -> tuple:
    if st.session_state.sort_mode == "Priority":
        return (PRIORITY_RANK[task["priority"]], -timestamp(task["created_at"]))
    if st.session_state.sort_mode == "Due date":
        return (due_timestamp(task["due_date"]), -timestamp(task["created_at"]))
    return (-timestamp(task["created_at"]),)


def due_state(due_value: str, status: str) -> tuple[str, str]:
    if not due_value:
        return "No due date", "pill"
    try:
        due = date.fromisoformat(due_value)
    except ValueError:
        return due_value, "pill"

    delta = (due - date.today()).days
    if status == "Done":
        return due.strftime("%b %d"), "pill done"
    if delta < 0:
        return f"Overdue by {abs(delta)}d", "pill warn"
    if delta == 0:
        return "Due today", "pill warn"
    if delta == 1:
        return "Due tomorrow", "pill"
    return due.strftime("%b %d"), "pill"


def export_csv(tasks: list[dict[str, Any]]) -> bytes:
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["title", "notes", "status", "priority", "due_date", "created_at", "updated_at"])
    for task in tasks:
        writer.writerow(
            [
                task["title"],
                task["notes"],
                task["status"],
                task["priority"],
                task["due_date"],
                task["created_at"],
                task["updated_at"],
            ]
        )
    return buffer.getvalue().encode("utf-8")


set_page_style()
ensure_state()

st.markdown(
    """
    <div class="hero">
      <h1>Focus Board</h1>
      <p>An interactive task tracker for simple planning, progress, and follow-through.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

visible_tasks = [task for task in st.session_state.tasks if matches_filters(task)]
ordered_tasks = sorted(visible_tasks, key=sort_key)

total = len(st.session_state.tasks)
done = sum(1 for task in st.session_state.tasks if task["status"] == "Done")
open_tasks = total - done
overdue = sum(
    1
    for task in st.session_state.tasks
    if task["status"] != "Done" and task["due_date"] and due_timestamp(task["due_date"]) < due_timestamp(date.today().isoformat())
)

metric_cols = st.columns(4)
metric_data = [
    ("Total tasks", total),
    ("Open tasks", open_tasks),
    ("Done", done),
    ("Overdue", overdue),
]
for column, (label, value) in zip(metric_cols, metric_data, strict=True):
    with column:
        st.markdown(
            f'<div class="metric"><div class="label">{label}</div><div class="value">{value}</div></div>',
            unsafe_allow_html=True,
        )

sidebar = st.sidebar
sidebar.header("Task editor")
if st.session_state.editing_task_id:
    sidebar.button("Cancel editing", on_click=reset_form, use_container_width=True)

with sidebar.form("task_editor", clear_on_submit=False):
    st.text_input("Task title", key="form_title", placeholder="Add a clear task title")
    st.text_area("Notes", key="form_notes", height=110, placeholder="Optional details")
    st.selectbox("Status", STATUS_OPTIONS, key="form_status")
    st.selectbox("Priority", PRIORITY_OPTIONS, key="form_priority")
    st.date_input("Due date", key="form_due_date", value=st.session_state.form_due_date)
    submit_label = "Save changes" if st.session_state.editing_task_id else "Add task"
    submitted = st.form_submit_button(submit_label, use_container_width=True)
    if submitted:
        upsert_task()
        st.rerun()

sidebar.divider()
sidebar.subheader("View")
st.session_state.search_query = sidebar.text_input(
    "Search",
    value=st.session_state.search_query,
    placeholder="Search title or notes",
)
st.session_state.status_filter = sidebar.radio(
    "Status filter",
    ["All", "Open", "Done"],
    horizontal=True,
    index=["All", "Open", "Done"].index(st.session_state.status_filter),
)
st.session_state.sort_mode = sidebar.selectbox(
    "Sort by",
    ["Newest", "Due date", "Priority"],
    index=["Newest", "Due date", "Priority"].index(st.session_state.sort_mode),
)

sidebar.divider()
if sidebar.button("Load sample tasks", use_container_width=True):
    load_samples()
    st.rerun()

sidebar.download_button(
    "Download CSV",
    data=export_csv(st.session_state.tasks),
    file_name="focus-board-tasks.csv",
    mime="text/csv",
    use_container_width=True,
)

if not ordered_tasks:
    st.info("No tasks match the current filters. Add a task or widen the search.")
else:
    for task in ordered_tasks:
        title_class = "task-title done" if task["status"] == "Done" else "task-title"
        due_label, due_class = due_state(task["due_date"], task["status"])
        priority_class = task["priority"].lower()

        with st.container():
            st.markdown('<div class="task-card">', unsafe_allow_html=True)
            st.markdown(f'<div class="{title_class}">{task["title"]}</div>', unsafe_allow_html=True)
            if task["notes"]:
                st.markdown(f'<div class="subtle">{task["notes"]}</div>', unsafe_allow_html=True)
            st.markdown(
                f"""
                <div class="task-meta">
                  <span class="pill {priority_class}">{task["priority"]} priority</span>
                  <span class="{due_class}">{due_label}</span>
                  <span class="pill">{task["status"]}</span>
                </div>
                """,
                unsafe_allow_html=True,
            )

            action_cols = st.columns([1, 1, 1, 1, 2])
            with action_cols[0]:
                if task["status"] == "Done":
                    if st.button("Reopen", key=f"reopen_{task['id']}", use_container_width=True):
                        set_status(task["id"], "Open")
                        st.rerun()
                else:
                    if st.button("Done", key=f"done_{task['id']}", use_container_width=True):
                        set_status(task["id"], "Done")
                        st.rerun()
            with action_cols[1]:
                if task["status"] != "In Progress":
                    if st.button("Start", key=f"start_{task['id']}", use_container_width=True):
                        set_status(task["id"], "In Progress")
                        st.rerun()
                else:
                    st.button("In progress", key=f"progress_{task['id']}", use_container_width=True, disabled=True)
            with action_cols[2]:
                if st.button("Edit", key=f"edit_{task['id']}", use_container_width=True):
                    set_editor(task["id"])
                    st.rerun()
            with action_cols[3]:
                if st.button("Delete", key=f"delete_{task['id']}", use_container_width=True):
                    remove_task(task["id"])
                    st.rerun()
            with action_cols[4]:
                st.caption(f"Updated {task['updated_at']}")
            st.markdown("</div>", unsafe_allow_html=True)

