async function fetchJSON(url, options) {
  const res = await fetch(url, options);
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

let editingNoteId = null;

function showEditForm(note) {
  editingNoteId = note.id;
  document.getElementById('edit-title').value = note.title;
  document.getElementById('edit-content').value = note.content;
  document.getElementById('edit-form').style.display = 'block';
}

function hideEditForm() {
  editingNoteId = null;
  document.getElementById('edit-title').value = '';
  document.getElementById('edit-content').value = '';
  document.getElementById('edit-form').style.display = 'none';
}

async function loadNotes(searchQuery = '') {
  const list = document.getElementById('notes');
  list.innerHTML = '';
  const url = searchQuery ? `/notes/search?q=${encodeURIComponent(searchQuery)}` : '/notes/';
  const notes = await fetchJSON(url);
  for (const n of notes) {
    const li = document.createElement('li');
    li.innerHTML = `<strong>${n.title}</strong>: ${n.content}`;
    
    const editBtn = document.createElement('button');
    editBtn.textContent = 'Edit';
    editBtn.onclick = () => showEditForm(n);
    editBtn.style.marginLeft = '8px';
    
    const delBtn = document.createElement('button');
    delBtn.textContent = 'Delete';
    delBtn.onclick = async () => {
      if (confirm('Delete this note?')) {
        await fetch(`/notes/${n.id}`, { method: 'DELETE' });
        loadNotes();
      }
    };
    delBtn.style.marginLeft = '4px';
    
    li.appendChild(editBtn);
    li.appendChild(delBtn);
    list.appendChild(li);
  }
}

async function loadActions() {
  const list = document.getElementById('actions');
  list.innerHTML = '';
  const items = await fetchJSON('/action-items/');
  for (const a of items) {
    const li = document.createElement('li');
    li.textContent = `${a.description} [${a.completed ? 'done' : 'open'}]`;
    if (!a.completed) {
      const btn = document.createElement('button');
      btn.textContent = 'Complete';
      btn.onclick = async () => {
        await fetchJSON(`/action-items/${a.id}/complete`, { method: 'PUT' });
        loadActions();
      };
      li.appendChild(btn);
    }
    list.appendChild(li);
  }
}

window.addEventListener('DOMContentLoaded', () => {
  document.getElementById('note-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const title = document.getElementById('note-title').value;
    const content = document.getElementById('note-content').value;
    await fetchJSON('/notes/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ title, content }),
    });
    e.target.reset();
    loadNotes();
  });

  document.getElementById('search-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const query = document.getElementById('search-input').value;
    loadNotes(query);
  });

  document.getElementById('clear-search').addEventListener('click', () => {
    document.getElementById('search-input').value = '';
    loadNotes();
  });

  document.getElementById('save-edit').addEventListener('click', async () => {
    const title = document.getElementById('edit-title').value;
    const content = document.getElementById('edit-content').value;
    if (title && content && editingNoteId) {
      await fetch(`/notes/${editingNoteId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ title, content }),
      });
      hideEditForm();
      loadNotes();
    }
  });

  document.getElementById('cancel-edit').addEventListener('click', hideEditForm);

  document.getElementById('action-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const description = document.getElementById('action-desc').value;
    await fetchJSON('/action-items/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ description }),
    });
    e.target.reset();
    loadActions();
  });

  loadNotes();
  loadActions();
});
