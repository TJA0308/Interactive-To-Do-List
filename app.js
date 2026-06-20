const TODO_STORAGE_KEY = "focus-board:tasks";
const THEME_STORAGE_KEY = "focus-board:theme";

const form = document.querySelector("#task-form");
const taskInput = document.querySelector("#task-input");
const priorityInput = document.querySelector("#priority-input");
const dueInput = document.querySelector("#due-input");
const submitButton = document.querySelector("#submit-button");
const cancelEditButton = document.querySelector("#cancel-edit");
const searchInput = document.querySelector("#search-input");
const sortInput = document.querySelector("#sort-input");
const taskList = document.querySelector("#task-list");
const template = document.querySelector("#task-template");
const emptyState = document.querySelector("#empty-state");
const clearCompletedButton = document.querySelector("#clear-completed");
const seedTasksButton = document.querySelector("#seed-tasks");
const themeToggle = document.querySelector("#theme-toggle");
const filterButtons = document.querySelectorAll(".filter-button");
const progressRing = document.querySelector("#progress-ring");
const progressPercent = document.querySelector("#progress-percent");
const progressCopy = document.querySelector("#progress-copy");
const totalCount = document.querySelector("#total-count");
const activeCount = document.querySelector("#active-count");
const doneCount = document.querySelector("#done-count");

const priorityRank = {
  high: 0,
  normal: 1,
  low: 2,
};

let tasks = loadTasks();
let activeFilter = "all";
let editingId = null;

applySavedTheme();
renderTasks();

form.addEventListener("submit", (event) => {
  event.preventDefault();

  const title = taskInput.value.trim();
  if (!title) return;

  if (editingId) {
    tasks = tasks.map((task) => (
      task.id === editingId
        ? {
            ...task,
            title,
            priority: priorityInput.value,
            dueDate: dueInput.value,
          }
        : task
    ));
    stopEditing();
  } else {
    tasks.unshift({
      id: createTaskId(),
      title,
      priority: priorityInput.value,
      dueDate: dueInput.value,
      completed: false,
      createdAt: Date.now(),
    });
    form.reset();
    priorityInput.value = "normal";
  }

  persistAndRender();
});

cancelEditButton.addEventListener("click", () => {
  stopEditing();
});

searchInput.addEventListener("input", () => {
  renderTasks();
});

sortInput.addEventListener("change", () => {
  renderTasks();
});

filterButtons.forEach((button) => {
  button.addEventListener("click", () => {
    activeFilter = button.dataset.filter;
    filterButtons.forEach((filterButton) => {
      filterButton.classList.toggle("active", filterButton === button);
    });
    renderTasks();
  });
});

taskList.addEventListener("change", (event) => {
  if (!event.target.classList.contains("task-check")) return;

  const item = event.target.closest(".task-item");
  toggleTask(item.dataset.id, event.target.checked);
});

taskList.addEventListener("click", (event) => {
  const item = event.target.closest(".task-item");
  if (!item) return;

  if (event.target.classList.contains("delete-button")) {
    deleteTask(item.dataset.id);
  }

  if (event.target.classList.contains("edit-button")) {
    startEditing(item.dataset.id);
  }
});

clearCompletedButton.addEventListener("click", () => {
  tasks = tasks.filter((task) => !task.completed);
  persistAndRender();
});

seedTasksButton.addEventListener("click", () => {
  const today = new Date();
  const tomorrow = addDays(today, 1);
  const nextWeek = addDays(today, 7);

  tasks = [
    {
      id: createTaskId(),
      title: "Review project checklist",
      priority: "high",
      dueDate: formatDateInput(today),
      completed: false,
      createdAt: Date.now() + 3,
    },
    {
      id: createTaskId(),
      title: "Plan deployment steps",
      priority: "normal",
      dueDate: formatDateInput(tomorrow),
      completed: false,
      createdAt: Date.now() + 2,
    },
    {
      id: createTaskId(),
      title: "Archive finished notes",
      priority: "low",
      dueDate: formatDateInput(nextWeek),
      completed: true,
      createdAt: Date.now() + 1,
    },
    ...tasks,
  ];

  persistAndRender();
});

themeToggle.addEventListener("click", () => {
  const nextTheme = document.documentElement.dataset.theme === "dark" ? "light" : "dark";
  setTheme(nextTheme);
});

function loadTasks() {
  try {
    const saved = JSON.parse(localStorage.getItem(TODO_STORAGE_KEY));
    return Array.isArray(saved) ? saved : [];
  } catch {
    return [];
  }
}

function saveTasks() {
  localStorage.setItem(TODO_STORAGE_KEY, JSON.stringify(tasks));
}

function createTaskId() {
  if (globalThis.crypto && typeof globalThis.crypto.randomUUID === "function") {
    return globalThis.crypto.randomUUID();
  }

  return `${Date.now()}-${Math.random().toString(36).slice(2)}`;
}

function getVisibleTasks() {
  const query = searchInput.value.trim().toLowerCase();

  return tasks
    .filter((task) => {
      if (activeFilter === "active") return !task.completed;
      if (activeFilter === "completed") return task.completed;
      return true;
    })
    .filter((task) => task.title.toLowerCase().includes(query))
    .sort(sortTasks);
}

function sortTasks(a, b) {
  if (sortInput.value === "priority") {
    return priorityRank[a.priority] - priorityRank[b.priority] || b.createdAt - a.createdAt;
  }

  if (sortInput.value === "due") {
    return getDueRank(a.dueDate) - getDueRank(b.dueDate) || b.createdAt - a.createdAt;
  }

  return b.createdAt - a.createdAt;
}

function getDueRank(dueDate) {
  return dueDate ? new Date(`${dueDate}T00:00:00`).getTime() : Number.MAX_SAFE_INTEGER;
}

function renderTasks() {
  taskList.replaceChildren();

  const visibleTasks = getVisibleTasks();
  visibleTasks.forEach((task) => {
    const item = template.content.firstElementChild.cloneNode(true);
    const checkbox = item.querySelector(".task-check");
    const title = item.querySelector(".task-title");
    const priorityBadge = item.querySelector(".priority-badge");
    const dueBadge = item.querySelector(".due-badge");

    item.dataset.id = task.id;
    item.classList.toggle("completed", task.completed);
    item.classList.add(`priority-${task.priority}`);
    checkbox.checked = task.completed;
    title.textContent = task.title;

    priorityBadge.textContent = `${capitalize(task.priority)} priority`;
    priorityBadge.classList.add(task.priority);

    const dueState = getDueState(task.dueDate, task.completed);
    dueBadge.textContent = dueState.label;
    dueBadge.classList.toggle("today", dueState.state === "today");
    dueBadge.classList.toggle("overdue", dueState.state === "overdue");

    taskList.append(item);
  });

  updateMetrics();
  emptyState.style.display = visibleTasks.length ? "none" : "block";
  clearCompletedButton.disabled = tasks.every((task) => !task.completed);
  seedTasksButton.disabled = tasks.length > 0;
}

function updateMetrics() {
  const total = tasks.length;
  const completed = tasks.filter((task) => task.completed).length;
  const active = total - completed;
  const percent = total ? Math.round((completed / total) * 100) : 0;

  totalCount.textContent = total;
  activeCount.textContent = active;
  doneCount.textContent = completed;
  progressPercent.textContent = `${percent}%`;
  progressRing.style.setProperty("--progress", `${percent}%`);
  progressCopy.textContent = total ? `${completed} of ${total} complete` : "No tasks yet";
}

function toggleTask(id, completed) {
  tasks = tasks.map((task) => (
    task.id === id ? { ...task, completed } : task
  ));
  persistAndRender();
}

function deleteTask(id) {
  tasks = tasks.filter((task) => task.id !== id);
  if (editingId === id) stopEditing();
  persistAndRender();
}

function startEditing(id) {
  const task = tasks.find((item) => item.id === id);
  if (!task) return;

  editingId = id;
  taskInput.value = task.title;
  priorityInput.value = task.priority;
  dueInput.value = task.dueDate;
  submitButton.textContent = "Save";
  cancelEditButton.hidden = false;
  taskInput.focus();
}

function stopEditing() {
  editingId = null;
  form.reset();
  priorityInput.value = "normal";
  submitButton.textContent = "Add";
  cancelEditButton.hidden = true;
}

function getDueState(dueDate, completed) {
  if (!dueDate) {
    return { label: "No date", state: "none" };
  }

  const today = startOfDay(new Date());
  const due = startOfDay(new Date(`${dueDate}T00:00:00`));
  const diffDays = Math.round((due - today) / 86400000);

  if (!completed && diffDays < 0) {
    return { label: "Overdue", state: "overdue" };
  }

  if (diffDays === 0) {
    return { label: "Today", state: "today" };
  }

  if (diffDays === 1) {
    return { label: "Tomorrow", state: "soon" };
  }

  return { label: due.toLocaleDateString(undefined, { month: "short", day: "numeric" }), state: "dated" };
}

function applySavedTheme() {
  const savedTheme = localStorage.getItem(THEME_STORAGE_KEY);
  const fallbackTheme = window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
  setTheme(savedTheme || fallbackTheme);
}

function setTheme(theme) {
  document.documentElement.dataset.theme = theme;
  themeToggle.textContent = theme === "dark" ? "L" : "D";
  localStorage.setItem(THEME_STORAGE_KEY, theme);
}

function addDays(date, days) {
  const next = new Date(date);
  next.setDate(next.getDate() + days);
  return next;
}

function startOfDay(date) {
  return new Date(date.getFullYear(), date.getMonth(), date.getDate());
}

function formatDateInput(date) {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");

  return `${year}-${month}-${day}`;
}

function capitalize(value) {
  return value.charAt(0).toUpperCase() + value.slice(1);
}

function persistAndRender() {
  saveTasks();
  renderTasks();
}
