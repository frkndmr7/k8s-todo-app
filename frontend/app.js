// API URL - will be configured via environment variable in Kubernetes
const API_URL = window.ENV?.API_URL || 'http://localhost:8080';

let todos = [];

// Initialize app
document.addEventListener('DOMContentLoaded', () => {
    checkAPIHealth();
    fetchTodos();
    
    // Enter key support for input
    document.getElementById('todoInput').addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            addTodo();
        }
    });
});

// Check API health
async function checkAPIHealth() {
    const statusElement = document.getElementById('apiStatus');
    try {
        const response = await fetch(`${API_URL}/health`);
        if (response.ok) {
            statusElement.textContent = '✓ Connected';
            statusElement.classList.remove('error');
        } else {
            statusElement.textContent = '✗ Unhealthy';
            statusElement.classList.add('error');
        }
    } catch (error) {
        statusElement.textContent = '✗ Disconnected';
        statusElement.classList.add('error');
        console.error('API health check failed:', error);
    }
}

// Fetch all todos
async function fetchTodos() {
    try {
        const response = await fetch(`${API_URL}/api/todos`);
        if (!response.ok) {
            throw new Error('Failed to fetch todos');
        }
        todos = await response.json();
        renderTodos();
    } catch (error) {
        console.error('Error fetching todos:', error);
        showError('Failed to load todos. Check API connection.');
    }
}

// Add new todo
async function addTodo() {
    const input = document.getElementById('todoInput');
    const title = input.value.trim();
    
    if (!title) {
        input.focus();
        return;
    }
    
    try {
        const response = await fetch(`${API_URL}/api/todos`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ title, completed: false })
        });
        
        if (!response.ok) {
            throw new Error('Failed to create todo');
        }
        
        const newTodo = await response.json();
        todos.unshift(newTodo); // Add to beginning
        input.value = '';
        renderTodos();
    } catch (error) {
        console.error('Error adding todo:', error);
        showError('Failed to add todo');
    }
}

// Toggle todo completion
async function toggleTodo(id) {
    const todo = todos.find(t => t.id === id);
    if (!todo) return;
    
    try {
        const response = await fetch(`${API_URL}/api/todos/${id}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                title: todo.title,
                completed: !todo.completed
            })
        });
        
        if (!response.ok) {
            throw new Error('Failed to update todo');
        }
        
        const updatedTodo = await response.json();
        const index = todos.findIndex(t => t.id === id);
        if (index !== -1) {
            todos[index] = updatedTodo;
        }
        renderTodos();
    } catch (error) {
        console.error('Error toggling todo:', error);
        showError('Failed to update todo');
    }
}

// Delete todo
async function deleteTodo(id) {
    if (!confirm('Are you sure you want to delete this task?')) {
        return;
    }
    
    try {
        const response = await fetch(`${API_URL}/api/todos/${id}`, {
            method: 'DELETE'
        });
        
        if (!response.ok) {
            throw new Error('Failed to delete todo');
        }
        
        todos = todos.filter(t => t.id !== id);
        renderTodos();
    } catch (error) {
        console.error('Error deleting todo:', error);
        showError('Failed to delete todo');
    }
}

// Render todos to DOM
function renderTodos() {
    const todoList = document.getElementById('todoList');
    const emptyState = document.getElementById('emptyState');
    const totalCount = document.getElementById('totalCount');
    const completedCount = document.getElementById('completedCount');
    
    // Update stats
    const completed = todos.filter(t => t.completed).length;
    totalCount.textContent = `${todos.length} ${todos.length === 1 ? 'task' : 'tasks'}`;
    completedCount.textContent = `${completed} completed`;
    
    // Show/hide empty state
    if (todos.length === 0) {
        emptyState.classList.remove('hidden');
        todoList.innerHTML = '';
        return;
    } else {
        emptyState.classList.add('hidden');
    }
    
    // Render todo items
    todoList.innerHTML = todos.map(todo => `
        <li class="todo-item ${todo.completed ? 'completed' : ''}" data-id="${todo.id}">
            <input 
                type="checkbox" 
                ${todo.completed ? 'checked' : ''}
                onchange="toggleTodo(${todo.id})"
            >
            <span>${escapeHtml(todo.title)}</span>
            <button class="delete-btn" onclick="deleteTodo(${todo.id})">Delete</button>
        </li>
    `).join('');
}

// Show error message
function showError(message) {
    // Simple alert for now - could be improved with a toast notification
    alert(message);
}

// Escape HTML to prevent XSS
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}