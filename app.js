const STORAGE_KEY = "basic-todo-list:todos";

const form = document.querySelector("#todo-form");
const input = document.querySelector("#todo-input");
const list = document.querySelector("#todo-list");
const template = document.querySelector("#todo-template");
const remainingCount = document.querySelector("#remaining-count");
const emptyState = document.querySelector("#empty-state");
const clearCompletedButton = document.querySelector("#clear-completed");
const filterButtons = document.querySelectorAll(".filter-button");

let todos = loadTodos();
let currentFilter = "all";

form.addEventListener("submit", (event) => {
  event.preventDefault();

  const title = input.value.trim();
  if (!title) return;

  todos.unshift({
    id: createTodoId(),
    title,
    completed: false,
    createdAt: Date.now(),
  });

  input.value = "";
  persistAndRender();
});

filterButtons.forEach((button) => {
  button.addEventListener("click", () => {
    currentFilter = button.dataset.filter;
    filterButtons.forEach((item) => {
      item.classList.toggle("active", item === button);
    });
    renderTodos();
  });
});

clearCompletedButton.addEventListener("click", () => {
  todos = todos.filter((todo) => !todo.completed);
  persistAndRender();
});

function loadTodos() {
  try {
    const saved = JSON.parse(localStorage.getItem(STORAGE_KEY));
    return Array.isArray(saved) ? saved : [];
  } catch {
    return [];
  }
}

function createTodoId() {
  if (globalThis.crypto && typeof globalThis.crypto.randomUUID === "function") {
    return globalThis.crypto.randomUUID();
  }

  return `${Date.now()}-${Math.random().toString(36).slice(2)}`;
}

function saveTodos() {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(todos));
}

function getVisibleTodos() {
  if (currentFilter === "active") {
    return todos.filter((todo) => !todo.completed);
  }

  if (currentFilter === "completed") {
    return todos.filter((todo) => todo.completed);
  }

  return todos;
}

function renderTodos() {
  list.replaceChildren();

  const visibleTodos = getVisibleTodos();
  visibleTodos.forEach((todo) => {
    const item = template.content.firstElementChild.cloneNode(true);
    const checkbox = item.querySelector(".todo-check");
    const title = item.querySelector(".todo-title");
    const deleteButton = item.querySelector(".delete-button");

    item.classList.toggle("completed", todo.completed);
    checkbox.checked = todo.completed;
    title.textContent = todo.title;

    checkbox.addEventListener("change", () => {
      todo.completed = checkbox.checked;
      persistAndRender();
    });

    deleteButton.addEventListener("click", () => {
      todos = todos.filter((itemTodo) => itemTodo.id !== todo.id);
      persistAndRender();
    });

    list.append(item);
  });

  const remaining = todos.filter((todo) => !todo.completed).length;
  remainingCount.textContent = remaining;
  emptyState.style.display = visibleTodos.length ? "none" : "block";
  clearCompletedButton.disabled = todos.every((todo) => !todo.completed);
}

function persistAndRender() {
  saveTodos();
  renderTodos();
}

renderTodos();
