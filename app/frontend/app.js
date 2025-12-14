// Configurattion Details 
const API_URL = '/api'; 
let authToken = localStorage.getItem('authToken');
let currentUser = null;
let editingId = null;              // ID to track current active User
let editingRelationshipId = null;  // ID
let editingEventId = null;         // ID

const RELATION_TYPES = ['father', 'mother', 'brother', 'sister', 'husband', 'wife'];

function switchAuthTab(tab) {
    const msg = document.getElementById('authMessage');
    msg.style.display = 'none';

    const loginForm = document.getElementById('loginForm');
    const registerForm = document.getElementById('registerForm');
    const tabLogin = document.getElementById('tabLogin');
    const tabRegister = document.getElementById('tabRegister');

    if (tab === 'login') {
        loginForm.classList.remove('hidden');
        registerForm.classList.add('hidden');
        tabLogin.classList.add('active');
        tabRegister.classList.remove('active');
    } else {
        loginForm.classList.add('hidden');
        registerForm.classList.remove('hidden');
        tabLogin.classList.remove('active');
        tabRegister.classList.add('active');
    }
}

document.addEventListener('DOMContentLoaded', async () => {
    // relationship dropdown listeners
    document.getElementById('relPerson1').addEventListener('change', handleRelPersonSelectChange);
    document.getElementById('relPerson2').addEventListener('change', handleRelPersonSelectChange);

    // auth forms
    document.getElementById('loginForm').addEventListener('submit', onLoginSubmit);
    document.getElementById('registerForm').addEventListener('submit', onRegisterSubmit);

    // person form
    document.getElementById('personForm').addEventListener('submit', onPersonFormSubmit);

    // relationship form
    document.getElementById('relationshipForm').addEventListener('submit', onRelationshipFormSubmit);

    // event form
    document.getElementById('eventForm').addEventListener('submit', onEventFormSubmit);

    if (authToken) {
        const ok = await checkAuth();
        if (ok) {
            showApp();
            showHome();
        } else {
            showAuth();
        }
    } else {
        showAuth();
    }
});

// ===== AUTH LOGIC =====

async function checkAuth() {
    try {
        const r = await fetch(`${API_URL}/auth/me`, {
            headers: { 'Authorization': `Bearer ${authToken}` }
        });
        const res = await r.json();
        if (res.success) {
            currentUser = res.user;
            return true;
        } else {
            authToken = null;
            localStorage.removeItem('authToken');
            return false;
        }
    } catch (err) {
        return false;
    }
}

function showAuth() {
    document.getElementById('authScreen').classList.remove('hidden');
    document.getElementById('appScreen').classList.add('hidden');
    document.getElementById('loginForm').reset();
    document.getElementById('registerForm').reset();
}

function showApp() {
    document.getElementById('authScreen').classList.add('hidden');
    document.getElementById('appScreen').classList.remove('hidden');
    document.getElementById('currentUserName').textContent =
        currentUser.full_name || currentUser.username;
}

function showHome() {
    hideAllMainSections();
    document.getElementById('homePage').classList.remove('hidden');
}

function hideAllMainSections() {
    document.getElementById('homePage').classList.add('hidden');
    document.getElementById('profileSection').classList.add('hidden');
    document.getElementById('personFormSection').classList.add('hidden');
    document.getElementById('personViewSection').classList.add('hidden');
    document.getElementById('peopleSection').classList.add('hidden');
    document.getElementById('relationshipsSection').classList.add('hidden');
    document.getElementById('eventsSection').classList.add('hidden');
    document.getElementById('messageBox').style.display = 'none';
}

async function onLoginSubmit(e) {
    e.preventDefault();
    const username = document.getElementById('loginUsername').value;
    const password = document.getElementById('loginPassword').value;
    try {
        const r = await fetch(`${API_URL}/auth/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password })
        });
        const res = await r.json();
        if (res.success) {
            authToken = res.token;
            currentUser = res.user;
            localStorage.setItem('authToken', authToken);
            showApp();
            showHome();
        } else {
            showAuthMessage(res.error, 'error');
        }
    } catch (err) {
        showAuthMessage('Connection error: ' + err.message, 'error');
    }
}

async function onRegisterSubmit(e) {
    e.preventDefault();
    const username = document.getElementById('regUsername').value;
    const password = document.getElementById('regPassword').value;
    const email = document.getElementById('regEmail').value;
    const full_name = document.getElementById('regFullName').value;

    try {
        const r = await fetch(`${API_URL}/auth/register`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password, email, full_name })
        });
        const res = await r.json();
        if (res.success) {
            showAuthMessage('Registration successful. Please login.', 'success');
            setTimeout(() => {
                switchAuthTab('login');
                document.getElementById('loginUsername').value = username;
            }, 1000);
        } else {
            showAuthMessage(res.error, 'error');
        }
    } catch (err) {
        showAuthMessage('Connection error: ' + err.message, 'error');
    }
}

async function logout() {
    try {
        await fetch(`${API_URL}/auth/logout`, {
            method: 'POST',
            headers: { 'Authorization': `Bearer ${authToken}` }
        });
    } catch (e) {
        // ignore
    }
    authToken = null;
    currentUser = null;
    localStorage.removeItem('authToken');
    showAuth();
}

function showAuthMessage(message, type) {
    const m = document.getElementById('authMessage');
    m.textContent = message;
    m.className = 'message ' + (type === 'error' ? 'error' : 'success');
    m.style.display = 'block';
    setTimeout(() => { m.style.display = 'none'; }, 4000);
}

// ===== PROFILE =====

function toggleProfile() {
    const el = document.getElementById('profileSection');
    if (el.classList.contains('hidden')) {
        document.getElementById('profileFullName').value = currentUser.full_name || '';
        document.getElementById('profileEmail').value = currentUser.email || '';
        document.getElementById('profilePassword').value = '';
        hideAllMainSections();
        el.classList.remove('hidden');
    } else {
        el.classList.add('hidden');
        showHome();
    }
}

async function saveProfile() {
    const full_name = document.getElementById('profileFullName').value;
    const email = document.getElementById('profileEmail').value;
    const password = document.getElementById('profilePassword').value;
    const pm = document.getElementById('profileMsg');

    try {
        const r = await fetch(`${API_URL}/auth/me`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${authToken}`
            },
            body: JSON.stringify({ full_name, email, password })
        });
        const res = await r.json();
        if (res.success) {
            currentUser = res.user;
            document.getElementById('currentUserName').textContent =
                currentUser.full_name || currentUser.username;
            pm.textContent = 'Profile updated';
            pm.className = 'message success';
            pm.style.display = 'block';
            setTimeout(() => { pm.style.display = 'none'; }, 3000);
            toggleProfile();
        } else {
            pm.textContent = res.error || 'Error';
            pm.className = 'message error';
            pm.style.display = 'block';
        }
    } catch (err) {
        pm.textContent = 'Connection error: ' + err.message;
        pm.className = 'message error';
        pm.style.display = 'block';
    }
}

// ===== PEOPLE =====

function showAddPerson() {
    hideAllMainSections();
    document.getElementById('personFormSection').classList.remove('hidden');
    document.getElementById('formTitle').textContent = 'Add New Person';
    document.getElementById('submitBtn').textContent = 'Add Person';
    resetForm();
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

function showPeople() {
    hideAllMainSections();
    document.getElementById('peopleSection').classList.remove('hidden');
    loadPeople();
}

function toggleDeathDate() {
    const status = document.getElementById('lifeStatus').value;
    const group = document.getElementById('deathDateGroup');

    if (status === 'deceased') {
        group.classList.remove('hidden');
    } else {
        group.classList.add('hidden');
        document.getElementById('deathDate').value = '';
    }
}

async function onPersonFormSubmit(e) {
    e.preventDefault();
    const status = document.getElementById('lifeStatus').value;

    const personData = {
        given_name: document.getElementById('givenName').value,
        family_name: document.getElementById('familyName').value,
        other_names: document.getElementById('otherNames').value,
        gender: document.getElementById('gender').value,
        birth_date: document.getElementById('birthDate').value || null,
        death_date: (status === 'deceased'
            ? document.getElementById('deathDate').value || null
            : null
        ),
        birth_place: document.getElementById('birthPlace').value,
        bio: document.getElementById('bio').value,
        relation: document.getElementById('relation').value
    };

    const hiddenId = document.getElementById('personId').value;
    const idToUse = editingId || (hiddenId ? parseInt(hiddenId, 10) : null);

    if (idToUse) {
        await updatePerson(idToUse, personData);
    } else {
        await createPerson(personData);
    }
}

async function createPerson(personData) {
    try {
        const r = await fetch(`${API_URL}/people`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${authToken}`
            },
            body: JSON.stringify(personData)
        });
        const res = await r.json();
        if (res.success) {
            showMessage('Person added', 'success');
            resetForm();
            showPeople();
        } else {
            showMessage('Error: ' + res.error, 'error');
        }
    } catch (err) {
        showMessage('Connection error: ' + err.message, 'error');
    }
}

async function loadPeople() {
    const container = document.getElementById('peopleList');
    container.innerHTML = '<div>Loading...</div>';
    try {
        const r = await fetch(`${API_URL}/people`, {
            headers: { 'Authorization': `Bearer ${authToken}` }
        });
        const res = await r.json();
        if (res.success) {
            displayPeople(res.data);
        } else {
            if (r.status === 401) { logout(); }
            container.innerHTML = `<div class="message error">${res.error}</div>`;
        }
    } catch (err) {
        container.innerHTML = `<div class="message error">Connection error: ${err.message}</div>`;
    }
}

function displayPeople(people) {
    const container = document.getElementById('peopleList');
    if (!people || people.length === 0) {
        container.innerHTML = '<div>No people found. Click "Add Person" to create one.</div>';
        return;
    }
    let html = `<table><thead><tr><th>Name</th><th>Relation</th><th>Birth Date</th><th>Birth Place</th><th>Gender</th><th>Actions</th></tr></thead><tbody>`;
    people.forEach(p => {
        const name = `${p.given_name} ${p.family_name}`;
        const birthDate = p.birth_date ? new Date(p.birth_date).toLocaleDateString() : 'N/A';
        html += `<tr>
            <td><strong>${escapeHtml(name)}</strong></td>
            <td>${escapeHtml(p.relation || 'N/A')}</td>
            <td>${birthDate}</td>
            <td>${escapeHtml(p.birth_place || 'N/A')}</td>
            <td>${escapeHtml(p.gender || 'N/A')}</td>
            <td class="actions">
                <button onclick="viewPerson(${p.id})">View</button>
                <button onclick="editPerson(${p.id})">Edit</button>
                <button class="delete" onclick="deletePerson(${p.id}, '${escapeJs(name)}')">Delete</button>
            </td>
        </tr>`;
    });
    html += '</tbody></table>';
    container.innerHTML = html;
}

async function viewPerson(id) {
    try {
        const r = await fetch(`${API_URL}/people/${id}`, {
            headers: { 'Authorization': `Bearer ${authToken}` }
        });
        const res = await r.json();
        if (res.success) {
            const p = res.data;

            // compute status from death_date
            const status = p.death_date ? 'Deceased' : 'Alive';

            hideAllMainSections();
            document.getElementById('personViewSection').classList.remove('hidden');

            document.getElementById('viewPersonId').value = p.id;
            document.getElementById('viewFullName').textContent = `${p.given_name} ${p.family_name}`;
            document.getElementById('viewOtherNames').textContent = p.other_names || '';
            document.getElementById('viewGender').textContent = p.gender || '';
            document.getElementById('viewStatus').textContent = status;
            document.getElementById('viewBirthDate').textContent =
                p.birth_date ? new Date(p.birth_date).toLocaleDateString() : '';
            document.getElementById('viewDeathDate').textContent =
                p.death_date ? new Date(p.death_date).toLocaleDateString() : '';
            document.getElementById('viewBirthPlace').textContent = p.birth_place || '';
            document.getElementById('viewRelation').textContent = p.relation || '';
            document.getElementById('viewBio').textContent = p.bio || '';
        } else {
            showMessage('Error: ' + res.error, 'error');
        }
    } catch (err) {
        showMessage('Connection error: ' + err.message, 'error');
    }
}

async function editPerson(id) {
    try {
        const r = await fetch(`${API_URL}/people/${id}`, {
            headers: { 'Authorization': `Bearer ${authToken}` }
        });
        const res = await r.json();
        if (res.success) {
            const p = res.data;
            editingId = id;
            hideAllMainSections();
            document.getElementById('personFormSection').classList.remove('hidden');
            document.getElementById('formTitle').textContent = 'Edit Person';
            document.getElementById('submitBtn').textContent = 'Update Person';
            document.getElementById('personId').value = id;
            document.getElementById('givenName').value = p.given_name || '';
            document.getElementById('familyName').value = p.family_name || '';
            document.getElementById('otherNames').value = p.other_names || '';
            document.getElementById('gender').value = p.gender || '';
            document.getElementById('birthDate').value = p.birth_date ? p.birth_date.split('T')[0] : (p.birth_date || '');
            document.getElementById('birthPlace').value = p.birth_place || '';
            document.getElementById('bio').value = p.bio || '';
            document.getElementById('relation').value = p.relation || '';

            if (p.death_date) {
                document.getElementById('lifeStatus').value = 'deceased';
                document.getElementById('deathDate').value = p.death_date.split('T')[0];
            } else {
                document.getElementById('lifeStatus').value = 'alive';
                document.getElementById('deathDate').value = '';
            }
            toggleDeathDate();

            window.scrollTo({ top: 0, behavior: 'smooth' });
        } else {
            showMessage('Error: ' + res.error, 'error');
        }
    } catch (err) {
        showMessage('Connection error: ' + err.message, 'error');
    }
}

async function updatePerson(id, personData) {
    try {
        const r = await fetch(`${API_URL}/people/${id}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${authToken}`
            },
            body: JSON.stringify(personData)
        });
        const res = await r.json();
        if (res.success) {
            showMessage('Person updated', 'success');
            resetForm();
            showPeople();
        } else {
            showMessage('Error: ' + res.error, 'error');
        }
    } catch (err) {
        showMessage('Connection error: ' + err.message, 'error');
    }
}

async function deletePerson(id, name) {
    if (!confirm(`Delete ${name}?`)) return;
    try {
        const r = await fetch(`${API_URL}/people/${id}`, {
            method: 'DELETE',
            headers: { 'Authorization': `Bearer ${authToken}` }
        });
        const res = await r.json();
        if (res.success) {
            showMessage('Person deleted', 'success');
            loadPeople();
        } else {
            showMessage('Error: ' + res.error, 'error');
        }
    } catch (err) {
        showMessage('Connection error: ' + err.message, 'error');
    }
}

function resetForm() {
    editingId = null;
    document.getElementById('personForm').reset();
    document.getElementById('formTitle').textContent = 'Add New Person';
    document.getElementById('submitBtn').textContent = 'Add Person';
    document.getElementById('personId').value = '';
    document.getElementById('lifeStatus').value = 'alive';
    toggleDeathDate();
}

function cancelAddEdit() {
    resetForm();
    showHome();
}

function showMessage(msg, type) {
    const box = document.getElementById('messageBox');
    box.textContent = msg;
    box.className = 'message ' + (type === 'error' ? 'error' : 'success');
    box.style.display = 'block';
    setTimeout(() => { box.style.display = 'none'; }, 4000);
}

// ===== RELATIONSHIPS =====

// separate views for add vs view
function showAddRelationship() {
    hideAllMainSections();
    document.getElementById('relationshipsSection').classList.remove('hidden');
    document.getElementById('relationshipForm').classList.remove('hidden');
    document.getElementById('relationshipsList').classList.add('hidden');
    fillRelationTypes();
    loadPeopleOptionsForRelationships();
    resetRelationshipForm();
}

function showViewRelationships() {
    hideAllMainSections();
    document.getElementById('relationshipsSection').classList.remove('hidden');
    document.getElementById('relationshipForm').classList.add('hidden');
    document.getElementById('relationshipsList').classList.remove('hidden');
    loadRelationships();
}

function showRelationships() {
    showViewRelationships();
}

function fillRelationTypes() {
    const sel = document.getElementById('relType');
    if (!sel) return;
    sel.innerHTML = '<option value="">Select relation...</option>';
    RELATION_TYPES.forEach(t => {
        const opt = document.createElement('option');
        opt.value = t;
        opt.textContent = t.charAt(0).toUpperCase() + t.slice(1);
        sel.appendChild(opt);
    });
}

async function loadPeopleOptionsForRelationships() {
    try {
        const r = await fetch(`${API_URL}/people`, {
            headers: { 'Authorization': `Bearer ${authToken}` }
        });
        const res = await r.json();
        if (!res.success) {
            showRelMessage(res.error || 'Failed to load people', 'error');
            return;
        }
        const people = res.data || [];
        fillPersonSelect('relPerson1', people);
        fillPersonSelect('relPerson2', people);
    } catch (err) {
        showRelMessage('Connection error: ' + err.message, 'error');
    }
}

function fillPersonSelect(selectId, people) {
    const sel = document.getElementById(selectId);
    if (!sel) return;
    sel.innerHTML = '<option value="">Select person...</option>';
    people.forEach(p => {
        const opt = document.createElement('option');
        opt.value = p.id;
        opt.textContent = `${p.given_name} ${p.family_name}`;
        sel.appendChild(opt);
    });
    const optNew = document.createElement('option');
    optNew.value = '__new__';
    optNew.textContent = '➕ Add new person…';
    sel.appendChild(optNew);
}

function handleRelPersonSelectChange(event) {
    if (event.target.value === '__new__') {
        showAddPerson();
        event.target.value = '';
    }
}

async function onRelationshipFormSubmit(e) {
    e.preventDefault();
    const person1_id = parseInt(document.getElementById('relPerson1').value || '0', 10);
    const person2_id = parseInt(document.getElementById('relPerson2').value || '0', 10);
    const type = document.getElementById('relType').value;
    const details = document.getElementById('relDetails').value;

    if (!person1_id || !person2_id || !type) {
        showRelMessage('Both people and relation are required', 'error');
        return;
    }

    const payload = { person1_id, person2_id, type, details };

    if (editingRelationshipId) {
        await updateRelationship(editingRelationshipId, payload);
    } else {
        await createRelationship(payload);
    }
}

async function loadRelationships() {
    const container = document.getElementById('relationshipsList');
    container.innerHTML = 'Loading relationships...';
    try {
        const r = await fetch(`${API_URL}/relationships`, {
            headers: { 'Authorization': `Bearer ${authToken}` }
        });
        const res = await r.json();
        if (!res.success) {
            container.innerHTML = `<div class="message error">${res.error || 'Error loading relationships'}</div>`;
            return;
        }
        const rels = res.data || [];
        displayRelationships(rels);
    } catch (err) {
        container.innerHTML = `<div class="message error">Connection error: ${err.message}</div>`;
    }
}

function displayRelationships(rels) {
    const container = document.getElementById('relationshipsList');
    if (!rels.length) {
        container.innerHTML = '<div>No relationships found. Use "Add Relationship" to create one.</div>';
        return;
    }
    let html = `<table><thead><tr>
        <th>Person</th>
        <th>Relation</th>
        <th>Person to whom related</th>
        <th>Details</th>
        <th>Actions</th>
    </tr></thead><tbody>`;
    rels.forEach(r => {
        html += `<tr>
            <td>${escapeHtml(r.person1_name || '')}</td>
            <td>${escapeHtml((r.type || '').charAt(0).toUpperCase() + (r.type || '').slice(1))}</td>
            <td>${escapeHtml(r.person2_name || '')}</td>
            <td>${escapeHtml(r.details || '')}</td>
            <td class="actions">
                <button class="small" onclick="editRelationship(${r.id})">Edit</button>
                <button class="small delete" onclick="deleteRelationship(${r.id})">Delete</button>
            </td>
        </tr>`;
    });
    html += '</tbody></table>';
    container.innerHTML = html;
}

async function editRelationship(id) {
    showAddRelationship();
    try {
        const r = await fetch(`${API_URL}/relationships/${id}`, {
            headers: { 'Authorization': `Bearer ${authToken}` }
        });
        const res = await r.json();
        if (!res.success) {
            showRelMessage(res.error || 'Error loading relationship', 'error');
            return;
        }
        const rel = res.data;
        editingRelationshipId = id;
        document.getElementById('relationshipId').value = id;
        fillRelationTypes();
        await loadPeopleOptionsForRelationships();

        document.getElementById('relPerson1').value = rel.person1_id;
        document.getElementById('relPerson2').value = rel.person2_id;
        document.getElementById('relType').value = (rel.type || '').toLowerCase();
        document.getElementById('relDetails').value = rel.details || '';

        document.getElementById('relSubmitBtn').textContent = 'Update Relationship';
    } catch (err) {
        showRelMessage('Connection error: ' + err.message, 'error');
    }
}

async function createRelationship(payload) {
    try {
        const r = await fetch(`${API_URL}/relationships`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${authToken}`
            },
            body: JSON.stringify(payload)
        });
        const res = await r.json();
        if (res.success) {
            showRelMessage('Relationship added', 'success');
            resetRelationshipForm();
            loadRelationships();
        } else {
            showRelMessage(res.error || 'Error creating relationship', 'error');
        }
    } catch (err) {
        showRelMessage('Connection error: ' + err.message, 'error');
    }
}

async function updateRelationship(id, payload) {
    try {
        const r = await fetch(`${API_URL}/relationships/${id}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${authToken}`
            },
            body: JSON.stringify(payload)
        });
        const res = await r.json();
        if (res.success) {
            showRelMessage('Relationship updated', 'success');
            resetRelationshipForm();
            loadRelationships();
        } else {
            showRelMessage(res.error || 'Error updating relationship', 'error');
        }
    } catch (err) {
        showRelMessage('Connection error: ' + err.message, 'error');
    }
}

async function deleteRelationship(id) {
    if (!confirm('Delete this relationship?')) return;
    try {
        const r = await fetch(`${API_URL}/relationships/${id}`, {
            method: 'DELETE',
            headers: { 'Authorization': `Bearer ${authToken}` }
        });
        const res = await r.json();
        if (res.success) {
            showRelMessage('Relationship deleted', 'success');
            loadRelationships();
        } else {
            showRelMessage(res.error || 'Error deleting relationship', 'error');
        }
    } catch (err) {
        showRelMessage('Connection error: ' + err.message, 'error');
    }
}

function resetRelationshipForm() {
    editingRelationshipId = null;
    const form = document.getElementById('relationshipForm');
    form.reset();
    document.getElementById('relationshipId').value = '';
    document.getElementById('relSubmitBtn').textContent = 'Add Relationship';
}

function showRelMessage(msg, type) {
    const box = document.getElementById('relMessage');
    box.textContent = msg;
    box.className = 'message ' + (type === 'error' ? 'error' : 'success');
    box.style.display = 'block';
    setTimeout(() => { box.style.display = 'none'; }, 4000);
}

// ===== EVENTS =====

function showAddEvent() {
    hideAllMainSections();
    document.getElementById('eventsSection').classList.remove('hidden');
    document.getElementById('eventForm').classList.remove('hidden');
    document.getElementById('eventsList').classList.add('hidden');
    loadPeopleOptionsForEvents();
    resetEventForm();
}

function showViewEvents() {
    hideAllMainSections();
    document.getElementById('eventsSection').classList.remove('hidden');
    document.getElementById('eventForm').classList.add('hidden');
    document.getElementById('eventsList').classList.remove('hidden');
    loadEvents();
}

async function loadPeopleOptionsForEvents() {
    try {
        const r = await fetch(`${API_URL}/people`, {
            headers: { 'Authorization': `Bearer ${authToken}` }
        });
        const res = await r.json();
        if (!res.success) {
            showEventMessage(res.error || 'Failed to load people', 'error');
            return;
        }
        const people = res.data || [];
        const sel = document.getElementById('eventPerson');
        sel.innerHTML = '<option value="">Select person...</option>';
        people.forEach(p => {
            const opt = document.createElement('option');
            opt.value = p.id;
            opt.textContent = `${p.given_name} ${p.family_name}`;
            sel.appendChild(opt);
        });
    } catch (err) {
        showEventMessage('Connection error: ' + err.message, 'error');
    }
}

async function onEventFormSubmit(e) {
    e.preventDefault();
    const person_id = parseInt(document.getElementById('eventPerson').value || '0', 10);
    const title = document.getElementById('eventTitle').value;
    const event_date = document.getElementById('eventDate').value || null;
    const place = document.getElementById('eventPlace').value;
    const description = document.getElementById('eventDescription').value;

    if (!person_id || !title) {
        showEventMessage('Person and title are required', 'error');
        return;
    }

    const payload = { created_by: person_id, title, event_date, place, description };

    if (editingEventId) {
        await updateEvent(editingEventId, payload);
    } else {
        await createEvent(payload);
    }
}

async function loadEvents() {
    const container = document.getElementById('eventsList');
    container.innerHTML = 'Loading events...';
    try {
        const r = await fetch(`${API_URL}/events`, {
            headers: { 'Authorization': `Bearer ${authToken}` }
        });
        const res = await r.json();
        if (!res.success) {
            container.innerHTML = `<div class="message error">${res.error || 'Error loading events'}</div>`;
            return;
        }
        const events = res.data || [];
        displayEvents(events);
    } catch (err) {
        container.innerHTML = `<div class="message error">Connection error: ${err.message}</div>`;
    }
}

function displayEvents(events) {
    const container = document.getElementById('eventsList');
    if (!events.length) {
        container.innerHTML = '<div>No events found. Use "Add Event" to create one.</div>';
        return;
    }
    let html = `<table><thead><tr>
        <th>Person</th>
        <th>Title</th>
        <th>Date</th>
        <th>Place</th>
        <th>Description</th>
        <th>Actions</th>
    </tr></thead><tbody>`;
    events.forEach(ev => {
        const dateText = ev.event_date || '';
        html += `<tr>
            <td>${escapeHtml(ev.person_name || '')}</td>
            <td>${escapeHtml(ev.title || '')}</td>
            <td>${escapeHtml(dateText)}</td>
            <td>${escapeHtml(ev.place || '')}</td>
            <td>${escapeHtml(ev.description || '')}</td>
            <td class="actions">
                <button class="small" onclick="editEvent(${ev.id})">Edit</button>
                <button class="small delete" onclick="deleteEvent(${ev.id})">Delete</button>
            </td>
        </tr>`;
    });
    html += '</tbody></table>';
    container.innerHTML = html;
}

async function editEvent(id) {
    showAddEvent();
    try {
        const r = await fetch(`${API_URL}/events/${id}`, {
            headers: { 'Authorization': `Bearer ${authToken}` }
        });
        const res = await r.json();
        if (!res.success) {
            showEventMessage(res.error || 'Error loading event', 'error');
            return;
        }
        const ev = res.data;
        editingEventId = id;
        document.getElementById('eventId').value = id;
        await loadPeopleOptionsForEvents();
        document.getElementById('eventPerson').value = ev.created_by;
        document.getElementById('eventTitle').value = ev.title || '';
        document.getElementById('eventDate').value = ev.event_date || '';
        document.getElementById('eventPlace').value = ev.place || '';
        document.getElementById('eventDescription').value = ev.description || '';
        document.getElementById('eventSubmitBtn').textContent = 'Update Event';
    } catch (err) {
        showEventMessage('Connection error: ' + err.message, 'error');
    }
}

async function createEvent(payload) {
    try {
        const r = await fetch(`${API_URL}/events`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${authToken}`
            },
            body: JSON.stringify(payload)
        });
        const res = await r.json();
        if (res.success) {
            showEventMessage('Event added', 'success');
            resetEventForm();
            loadEvents();
        } else {
            showEventMessage(res.error || 'Error creating event', 'error');
        }
    } catch (err) {
        showEventMessage('Connection error: ' + err.message, 'error');
    }
}

async function updateEvent(id, payload) {
    try {
        const r = await fetch(`${API_URL}/events/${id}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${authToken}`
            },
            body: JSON.stringify(payload)
        });
        const res = await r.json();
        if (res.success) {
            showEventMessage('Event updated', 'success');
            resetEventForm();
            loadEvents();
        } else {
            showEventMessage(res.error || 'Error updating event', 'error');
        }
    } catch (err) {
        showEventMessage('Connection error: ' + err.message, 'error');
    }
}

async function deleteEvent(id) {
    if (!confirm('Delete this event?')) return;
    try {
        const r = await fetch(`${API_URL}/events/${id}`, {
            method: 'DELETE',
            headers: { 'Authorization': `Bearer ${authToken}` }
        });
        const res = await r.json();
        if (res.success) {
            showEventMessage('Event deleted', 'success');
            loadEvents();
        } else {
            showEventMessage(res.error || 'Error deleting event', 'error');
        }
    } catch (err) {
        showEventMessage('Connection error: ' + err.message, 'error');
    }
}

function resetEventForm() {
    editingEventId = null;
    const form = document.getElementById('eventForm');
    form.reset();
    document.getElementById('eventId').value = '';
    document.getElementById('eventSubmitBtn').textContent = 'Add Event';
}

function showEventMessage(msg, type) {
    const box = document.getElementById('eventMessage');
    box.textContent = msg;
    box.className = 'message ' + (type === 'error' ? 'error' : 'success');
    box.style.display = 'block';
    setTimeout(() => { box.style.display = 'none'; }, 4000);
}

// ===== HELPERS =====

function escapeHtml(str) {
    if (!str) return '';
    return String(str).replace(/[&<>"']/g, function (m) {
        return ({
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#39;'
        }[m]);
    });
}

function escapeJs(str) {
    if (!str) return '';
    return String(str).replace(/'/g, "\\'");
}

