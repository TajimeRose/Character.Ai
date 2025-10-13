const storageKeys = {
    guestToken: 'aiCharacterGuestToken',
};

const state = {
    useGuest: String(window.APP_CONFIG?.useGuest ?? 'false').toLowerCase() === 'true',
    firebaseConfig: window.APP_CONFIG?.firebase || {},
    firebaseEnabled: String(window.APP_CONFIG?.firebaseEnabled ?? 'false').toLowerCase() === 'true',
    firebaseApp: null,
    firebaseAuth: null,
    idToken: null,
    user: null,
    drawerOpen: false,
    authMode: 'login',
    guestToken: null,
    page: document.body?.dataset?.page || 'home',
    chat: {
        character: window.CHAT_CONTEXT?.character || null,
        conversationId: window.CHAT_CONTEXT?.initialConversationId || null,
        messages: [],
        isTyping: false,
    },
    history: {
        items: [],
        loading: false,
    },
    elements: {},
};

function initFirebase() {
    // จัดการเริ่มต้น Firebase และสังเกตการเปลี่ยนสถานะการล็อกอิน
    if (!state.firebaseEnabled) {
        return;
    }
    if (typeof firebase === 'undefined' || !firebase?.initializeApp) {
        console.warn('Firebase SDK not loaded.');
        return;
    }
    try {
        state.firebaseApp = firebase.initializeApp(state.firebaseConfig);
        state.firebaseAuth = firebase.auth();
        state.firebaseAuth.onAuthStateChanged(async (user) => {
            state.user = user;
            if (user) {
                try {
                    state.idToken = await user.getIdToken();
                } catch (err) {
                    console.error('Unable to refresh ID token', err);
                    state.idToken = null;
                }
            } else {
                state.idToken = null;
            }
            renderNav();
            updateDrawerLogout();
        });
    } catch (error) {
        console.error('Failed to initialise Firebase', error);
    }
}

function ensureGuestToken() {
    // สร้างหรือดึงโทเค็นโหมดผู้เยี่ยมชมเพื่อใช้ยืนยันตัวตนชั่วคราว
    if (!state.useGuest) {
        return null;
    }
    if (state.guestToken) {
        return state.guestToken;
    }
    let token = localStorage.getItem(storageKeys.guestToken);
    if (!token) {
        const rand = (typeof crypto !== 'undefined' && crypto.randomUUID) ? crypto.randomUUID() : Math.random().toString(36).slice(2);
        token = `guest:${rand}`;
        localStorage.setItem(storageKeys.guestToken, token);
    }
    state.guestToken = token;
    return token;
}

function cacheElements() {
    // จับองค์ประกอบ DOM ที่ต้องใช้บ่อยเก็บไว้เพื่อลดการค้นหาซ้ำ
    state.elements.menuToggle = document.getElementById('menuToggle');
    state.elements.drawer = document.getElementById('drawer');
    state.elements.drawerOverlay = document.getElementById('drawerOverlay');
    state.elements.drawerLogout = document.getElementById('drawerLogout');
    state.elements.drawerLinks = document.querySelectorAll('.drawer-button[data-nav]');
    state.elements.navActions = document.getElementById('navActions');
    state.elements.closeDrawer = document.getElementById('closeDrawer');
    state.elements.authModal = document.getElementById('authModal');
    state.elements.authModalTitle = document.getElementById('authModalTitle');
    state.elements.authModalHelper = document.getElementById('authModalHelper');
    state.elements.authModalNote = document.getElementById('authModalNote');
    state.elements.inputDisplayName = document.getElementById('inputDisplayName');
    state.elements.inputEmail = document.getElementById('inputEmail');
    state.elements.inputPassword = document.getElementById('inputPassword');
    state.elements.cancelAuth = document.getElementById('cancelAuth');
    state.elements.saveAuth = document.getElementById('saveAuth');
    state.elements.toast = document.getElementById('toast');

    if (state.page === 'chat') {
        state.elements.chatLog = document.getElementById('chatLog');
        state.elements.chatInput = document.getElementById('chatInput');
        state.elements.sendButton = document.getElementById('sendButton');
        state.elements.typingIndicator = document.getElementById('typingIndicator');
        state.elements.chatEmpty = document.getElementById('chatEmpty');
        state.elements.startNewChat = document.getElementById('startNewChat');
    }
    if (state.page === 'history') {
        state.elements.historyList = document.getElementById('historyList');
        state.elements.refreshHistory = document.getElementById('refreshHistory');
    }
}

function renderNav() {
    // อัปเดตเมนูการนำทางให้เหมาะกับสถานะผู้ใช้ปัจจุบัน
    const nav = state.elements.navActions;
    if (!nav) {
        return;
    }
    nav.innerHTML = '';
    if (state.user && state.idToken) {
        const chip = document.createElement('div');
        chip.className = 'user-chip';
        chip.textContent = state.user.displayName || state.user.email || 'Connected';
        nav.appendChild(chip);
    } else {
        const loginBtn = document.createElement('button');
        loginBtn.className = 'secondary-button';
        loginBtn.type = 'button';
        loginBtn.dataset.action = 'login';
        loginBtn.textContent = 'Log in';
        const signupBtn = document.createElement('button');
        signupBtn.className = 'primary-button';
        signupBtn.type = 'button';
        signupBtn.dataset.action = 'signup';
        signupBtn.textContent = 'Sign up';
        nav.append(loginBtn, signupBtn);
    }
}

function updateDrawerLogout() {
    // สลับการแสดงปุ่มออกจากระบบตามสถานะการล็อกอิน
    if (!state.elements.drawerLogout) {
        return;
    }
    const shouldShow = Boolean(state.idToken && state.user);
    state.elements.drawerLogout.style.display = shouldShow ? 'block' : 'none';
}

function highlightDrawer() {
    // ทำให้เมนูในลิ้นชักไฮไลต์ตรงกับหน้าที่กำลังใช้งาน
    if (!state.elements.drawerLinks) {
        return;
    }
    state.elements.drawerLinks.forEach((link) => {
        link.classList.toggle('active', link.dataset.nav === state.page);
    });
}

function toggleDrawer(forceOpen) {
    // เปิดหรือปิดลิ้นชักนำทางและตั้งค่า state ให้สอดคล้อง
    const drawer = state.elements.drawer;
    const overlay = state.elements.drawerOverlay;
    if (!drawer || !overlay) {
        return;
    }
    const open = typeof forceOpen === 'boolean' ? forceOpen : !drawer.classList.contains('open');
    drawer.classList.toggle('open', open);
    overlay.classList.toggle('open', open);
    drawer.setAttribute('aria-hidden', open ? 'false' : 'true');
    state.drawerOpen = open;
}

function closeDrawer() {
    // สั่งให้ลิ้นชักนำทางปิดตัวลง
    toggleDrawer(false);
}

function openAuthModal(mode) {
    // เปิดโมดัลยืนยันตัวตนสำหรับล็อกอินหรือสมัครสมาชิก
    state.authMode = mode === 'signup' ? 'signup' : 'login';
    const modal = state.elements.authModal;
    if (!modal) {
        if (!state.firebaseEnabled) {
            showToast('Firebase authentication is not configured.');
        }
        return;
    }
    const isSignup = state.authMode === 'signup';
    state.elements.authModalTitle.textContent = isSignup ? 'Create your access link' : 'Log in to continue';
    state.elements.authModalHelper.textContent = isSignup
        ? 'Register with your email to keep conversations in sync.'
        : 'Sign in with your credentials to resume conversations everywhere.';
    state.elements.authModalNote.textContent = state.useGuest
        ? 'Guest mode keeps local progress only. Sign in to save across devices.'
        : 'Authentication is required to continue.';
    state.elements.inputDisplayName.value = '';
    state.elements.inputEmail.value = '';
    state.elements.inputPassword.value = '';
    modal.classList.add('open');
    modal.setAttribute('aria-hidden', 'false');
    state.elements.inputEmail.focus();
}

function closeAuthModal() {
    // ปิดโมดัลยืนยันตัวตนและรีเซ็ตสถานะที่เกี่ยวข้อง
    const modal = state.elements.authModal;
    if (!modal) {
        return;
    }
    modal.classList.remove('open');
    modal.setAttribute('aria-hidden', 'true');
}

function needsAuth() {
    // ตรวจสอบว่าผู้ใช้อยู่ในโหมดที่ต้องล็อกอินหรือไม่
    return !state.idToken && !state.useGuest;
}

function getAuthHeaders() {
    // จัดเตรียมส่วนหัว HTTP พร้อมโทเค็นของผู้ใช้หรือแขก
    const headers = { 'Content-Type': 'application/json' };
    if (state.idToken) {
        headers.Authorization = `Bearer ${state.idToken}`;
    } else {
        const guest = ensureGuestToken();
        if (guest) {
            headers.Authorization = `Bearer ${guest}`;
        }
    }
    return headers;
}

function showToast(message) {
    // แสดงข้อความแจ้งเตือนสั้น ๆ แบบทอสต์
    if (!state.elements.toast) {
        alert(message);
        return;
    }
    state.elements.toast.textContent = message;
    state.elements.toast.classList.add('show');
    setTimeout(() => {
        state.elements.toast.classList.remove('show');
    }, 3600);
}

async function saveAuth() {
    // ดำเนินการสมัครหรือเข้าสู่ระบบผ่าน Firebase Authentication
    if (!state.firebaseEnabled || !state.firebaseAuth) {
        showToast('Authentication is not configured on this deployment.');
        closeAuthModal();
        return;
    }
    const email = state.elements.inputEmail.value.trim();
    const password = state.elements.inputPassword.value.trim();
    const displayName = state.elements.inputDisplayName.value.trim();
    if (!email || !password) {
        state.elements.authModalNote.textContent = 'Please provide both email and password to continue.';
        return;
    }
    try {
        if (state.authMode === 'signup') {
            const result = await state.firebaseAuth.createUserWithEmailAndPassword(email, password);
            if (displayName) {
                await result.user.updateProfile({ displayName });
            }
        } else {
            const result = await state.firebaseAuth.signInWithEmailAndPassword(email, password);
            if (displayName && !result.user.displayName) {
                await result.user.updateProfile({ displayName });
            }
        }
        closeAuthModal();
        showToast('You are signed in. Let\'s continue.');
    } catch (error) {
        console.error('Auth error', error);
        state.elements.authModalNote.textContent = error?.message || 'We could not complete that request.';
    }
}

function logout() {
    // ออกจากระบบ Firebase เมื่อมีผู้ใช้ล็อกอินอยู่
    if (state.firebaseAuth && state.user) {
        state.firebaseAuth.signOut().catch((err) => console.error('Failed to sign out', err));
    }
}

function attachCommonEvents() {
    // เชื่อมต่ออีเวนต์หลักให้ปุ่มและองค์ประกอบในหน้า
    if (state.elements.menuToggle) {
        state.elements.menuToggle.addEventListener('click', () => toggleDrawer());
    }
    if (state.elements.drawerOverlay) {
        state.elements.drawerOverlay.addEventListener('click', () => toggleDrawer(false));
    }
    if (state.elements.closeDrawer) {
        state.elements.closeDrawer.addEventListener('click', () => toggleDrawer(false));
    }
    if (state.elements.drawerLogout) {
        state.elements.drawerLogout.addEventListener('click', () => {
            logout();
            closeDrawer();
        });
    }
    if (state.elements.navActions) {
        state.elements.navActions.addEventListener('click', (event) => {
            const target = event.target.closest('button[data-action]');
            if (!target) {
                return;
            }
            event.preventDefault();
            openAuthModal(target.dataset.action);
        });
    }
    if (state.elements.drawerLinks) {
        state.elements.drawerLinks.forEach((link) => {
            link.addEventListener('click', () => closeDrawer());
        });
    }
    if (state.elements.authModal) {
        state.elements.authModal.addEventListener('click', (event) => {
            if (event.target === state.elements.authModal) {
                closeAuthModal();
            }
        });
    }
    if (state.elements.cancelAuth) {
        state.elements.cancelAuth.addEventListener('click', closeAuthModal);
    }
    if (state.elements.saveAuth) {
        state.elements.saveAuth.addEventListener('click', saveAuth);
    }
    document.addEventListener('keydown', (event) => {
        if (event.key === 'Escape') {
            closeAuthModal();
            closeDrawer();
        }
    });
}

function autoResizeTextarea() {
    // ปรับขนาดกล่องป้อนข้อความตามความยาวเนื้อหาโดยอัตโนมัติ
    const input = state.elements.chatInput;
    if (!input) {
        return;
    }
    input.style.height = 'auto';
    input.style.height = `${Math.min(180, input.scrollHeight)}px`;
}

function createMessageElement(message) {
    // สร้างองค์ประกอบ DOM สำหรับแสดงข้อความแต่ละรายการในห้องแชท
    const container = document.createElement('div');
    container.className = `message ${message.role === 'user' ? 'user' : 'ai'}`;
    const bubble = document.createElement('div');
    bubble.className = 'bubble';
    bubble.textContent = message.text;
    container.appendChild(bubble);
    if (message.ts) {
        const ts = document.createElement('span');
        ts.className = 'timestamp';
        ts.textContent = formatTimestamp(message.ts);
        container.appendChild(ts);
    }
    return container;
}

function formatTimestamp(value) {
    // แปลงค่าวันเวลาของแชทให้อ่านง่าย
    if (!value) {
        return '';
    }
    const date = value instanceof Date ? value : new Date(value);
    if (Number.isNaN(date.getTime())) {
        return '';
    }
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

function renderMessages() {
    // วาดข้อความทั้งหมดในบทสนทนาลงในพื้นที่แชท
    const log = state.elements.chatLog;
    if (!log) {
        return;
    }
    log.innerHTML = '';
    if (!state.chat.messages.length) {
        if (state.elements.chatEmpty) {
            log.appendChild(state.elements.chatEmpty);
            state.elements.chatEmpty.style.display = 'block';
        }
        return;
    }
    state.chat.messages.forEach((message) => {
        const element = createMessageElement(message);
        log.appendChild(element);
    });
    log.scrollTop = log.scrollHeight;
}

function appendMessage(message) {
    // เพิ่มข้อความใหม่ลงในบันทึกและเลื่อนหน้าต่างตามความเหมาะสม
    state.chat.messages.push(message);
    if (state.elements.chatEmpty) {
        state.elements.chatEmpty.style.display = 'none';
    }
    const log = state.elements.chatLog;
    if (!log) {
        return;
    }
    const element = createMessageElement(message);
    const shouldStick = log.scrollTop + log.clientHeight >= log.scrollHeight - 60;
    log.appendChild(element);
    if (shouldStick) {
        log.scrollTop = log.scrollHeight;
    }
}

function setTyping(flag) {
    // ตั้งค่าสถานะว่าบอทกำลังพิมพ์และควบคุมปุ่มส่งข้อความ
    state.chat.isTyping = flag;
    if (state.elements.typingIndicator) {
        state.elements.typingIndicator.classList.toggle('active', flag);
    }
    if (state.elements.sendButton) {
        state.elements.sendButton.disabled = flag;
    }
}

async function sendMessage() {
    // ส่งข้อความของผู้ใช้ไปยังเซิร์ฟเวอร์และจัดการคำตอบที่ได้รับ
    if (!state.elements.chatInput || !state.elements.sendButton) {
        return;
    }
    if (!state.chat.character) {
        showToast('Choose a character before sending a message.');
        return;
    }
    if (state.chat.isTyping) {
        return;
    }
    const raw = state.elements.chatInput.value;
    const text = raw.trim();
    if (!text) {
        return;
    }
    if (needsAuth()) {
        openAuthModal('login');
        return;
    }
    state.elements.chatInput.value = '';
    autoResizeTextarea();
    const now = new Date();
    appendMessage({ role: 'user', text, ts: now });
    setTyping(true);
    let response;
    try {
        response = await fetch('/api/chat', {
            method: 'POST',
            headers: getAuthHeaders(),
            body: JSON.stringify({
                character_key: state.chat.character?.key,
                text,
                conversation_id: state.chat.conversationId || undefined,
            }),
        });
    } catch (error) {
        console.error('Network error', error);
        appendMessage({ role: 'assistant', text: 'Connection hiccup. Please check your network and try again.', ts: new Date() });
        setTyping(false);
        return;
    }
    let data;
    try {
        data = await response.json();
    } catch (error) {
        data = {};
    }
    if (!response.ok) {
        appendMessage({ role: 'assistant', text: data?.error || 'Our AI companion is unavailable right now. Try again soon.', ts: new Date() });
        setTyping(false);
        return;
    }
    state.chat.conversationId = data.conversation_id;
    appendMessage({ role: 'assistant', text: data.assistant || '', ts: new Date() });
    setTyping(false);
}

function resetChat() {
    // รีเซ็ตสถานะแชทเพื่อเริ่มบทสนทนาใหม่
    state.chat.conversationId = null;
    state.chat.messages = [];
    if (state.elements.chatInput) {
        state.elements.chatInput.value = '';
        autoResizeTextarea();
    }
    renderMessages();
    showToast('Started a fresh thread.');
}

async function fetchConversation(id) {
    // โหลดบทสนทนาจากเซิร์ฟเวอร์มาใส่ในสถานะปัจจุบัน
    if (!id) {
        return;
    }
    try {
        const response = await fetch(`/api/conversations/${id}`, {
            headers: getAuthHeaders(),
        });
        const data = await response.json();
        if (!response.ok) {
            showToast(data?.error || 'Could not load that conversation.');
            return;
        }
        state.chat.conversationId = data.id;
        state.chat.messages = (data.messages || []).map((msg) => ({
            role: msg.role === 'user' ? 'user' : 'ai',
            text: msg.text || '',
            ts: msg.ts,
        }));
        renderMessages();
    } catch (error) {
        console.error('Conversation load error', error);
        showToast('We hit a network issue while opening that conversation.');
    }
}

async function loadHistory() {
    // ดึงรายการประวัติการสนทนามาแสดงบนหน้า History
    if (state.history.loading) {
        return;
    }
    state.history.loading = true;
    const list = state.elements.historyList;
    if (list) {
        list.innerHTML = '<div class="history-empty">Loading conversations...</div>';
    }
    try {
        const response = await fetch('/api/conversations?limit=50', {
            headers: getAuthHeaders(),
        });
        const data = await response.json();
        if (!response.ok) {
            if (list) {
                list.innerHTML = `<div class="history-empty">${data?.error || 'Unable to load history.'}</div>`;
            }
            state.history.loading = false;
            return;
        }
        state.history.items = Array.isArray(data) ? data : [];
        renderHistory();
    } catch (error) {
        console.error('History load error', error);
        if (list) {
            list.innerHTML = '<div class="history-empty">Network hiccup. Please try again.</div>';
        }
    } finally {
        state.history.loading = false;
    }
}

function renderHistory() {
    // ประกอบ DOM ของรายการประวัติการสนทนา
    const list = state.elements.historyList;
    if (!list) {
        return;
    }
    list.innerHTML = '';
    if (!state.history.items.length) {
        list.innerHTML = '<div class="history-empty">No conversations yet. Start a new chat to create one.</div>';
        return;
    }
    state.history.items.forEach((item) => {
        const row = document.createElement('article');
        row.className = 'history-item';
        const info = document.createElement('div');
        info.className = 'history-item-info';
        const title = document.createElement('h3');
        title.className = 'history-item-title';
        title.textContent = item.title || item.character_name || item.character_key || 'Conversation';
        const meta = document.createElement('div');
        meta.className = 'history-item-meta';
        meta.textContent = `${item.character_name || item.character_key || 'Unknown'} - ${formatHistoryTime(item.updated_at)}`;
        info.append(title, meta);
        const actions = document.createElement('div');
        actions.className = 'history-item-actions';
        const openBtn = document.createElement('button');
        openBtn.className = 'primary-button';
        openBtn.type = 'button';
        openBtn.textContent = 'Open';
        openBtn.addEventListener('click', () => {
            window.location.href = `/chat/${encodeURIComponent(item.character_key)}?conversation=${encodeURIComponent(item.id)}`;
        });
        const deleteBtn = document.createElement('button');
        deleteBtn.className = 'secondary-button';
        deleteBtn.type = 'button';
        deleteBtn.textContent = 'Delete';
        deleteBtn.addEventListener('click', () => deleteConversation(item));
        actions.append(openBtn, deleteBtn);
        row.append(info, actions);
        list.appendChild(row);
    });
}

function formatHistoryTime(value) {
    // จัดรูปแบบเวลาในประวัติให้เข้าใจง่าย
    if (!value) {
        return 'Just now';
    }
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) {
        return value;
    }
    return date.toLocaleString([], { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });
}

async function deleteConversation(item) {
    // ลบบันทึกบทสนทนาที่เลือกและอัปเดตหน้าจอ
    if (!confirm('Delete this conversation? This cannot be undone.')) {
        return;
    }
    try {
        const response = await fetch(`/api/conversations/${item.id}`, {
            method: 'DELETE',
            headers: getAuthHeaders(),
        });
        if (!response.ok) {
            const data = await response.json().catch(() => ({}));
            showToast(data?.error || 'Unable to delete that conversation.');
            return;
        }
        showToast('Conversation deleted.');
        state.history.items = state.history.items.filter((row) => row.id !== item.id);
        renderHistory();
    } catch (error) {
        console.error('Delete error', error);
        showToast('We ran into a network issue while deleting that conversation.');
    }
}

function initChat() {
    // เตรียมอีเวนต์และข้อมูลเมื่อผู้ใช้อยู่ในหน้าแชท
    ensureGuestToken();
    if (state.elements.chatInput) {
        autoResizeTextarea();
        state.elements.chatInput.addEventListener('input', autoResizeTextarea);
        state.elements.chatInput.addEventListener('keydown', (event) => {
            if (event.key === 'Enter' && !event.shiftKey) {
                event.preventDefault();
                sendMessage();
            }
        });
    }
    if (state.elements.sendButton) {
        state.elements.sendButton.addEventListener('click', sendMessage);
    }
    if (state.elements.startNewChat) {
        state.elements.startNewChat.addEventListener('click', () => {
            resetChat();
        });
    }
    if (state.chat.conversationId) {
        fetchConversation(state.chat.conversationId);
    }
}

function initHistory() {
    // ตั้งค่าหน้า History และเชื่อมต่อการรีเฟรชข้อมูล
    ensureGuestToken();
    if (state.elements.refreshHistory) {
        state.elements.refreshHistory.addEventListener('click', loadHistory);
    }
    loadHistory();
}

function initialise() {
    // เรียกขั้นตอนเตรียมระบบทั้งหมดเมื่อหน้าเพจพร้อมใช้งาน
    cacheElements();
    highlightDrawer();
    renderNav();
    updateDrawerLogout();
    attachCommonEvents();
    ensureGuestToken();
    initFirebase();

    if (state.page === 'chat') {
        initChat();
    }
    if (state.page === 'history') {
        initHistory();
    }
}

document.addEventListener('DOMContentLoaded', initialise);

