// Nexus-AI Client Application
class NexusApp {
  constructor() {
    this.sessionId = null;
    this.ws = null;
    this.isGenerating = false;
    this.currentAssistantMessageEl = null;
    this.currentThoughtEl = null;
    this.currentContentEl = null;
    this.recognition = null;
    this.isListening = false;
    this.ttsEnabled = false;

    // Authentication State
    this.authToken = localStorage.getItem('nexus_auth_token') || null;
    this.currentUser = null;
    this.authMode = 'login'; // 'login' or 'register'

    this.initElements();
    this.initAuth();
    this.initSpeech();
    this.bindEvents();
  }

  initElements() {
    this.chatMessages = document.getElementById('chat-messages');
    this.userInput = document.getElementById('user-input');
    this.sendBtn = document.getElementById('send-btn');
    this.newChatBtn = document.getElementById('new-chat-btn');
    this.sessionsList = document.getElementById('sessions-list');
    this.micBtn = document.getElementById('mic-btn');
    this.ttsBtn = document.getElementById('tts-btn');
    this.uploadBtn = document.getElementById('upload-btn');
    this.fileInput = document.getElementById('file-input');

    // Modals
    this.settingsModal = document.getElementById('settings-modal');
    this.settingsBtn = document.getElementById('settings-btn');
    this.closeSettingsBtn = document.getElementById('close-settings-btn');
    this.saveSettingsBtn = document.getElementById('save-settings-btn');

    this.ragModal = document.getElementById('rag-modal');
    this.ragBtn = document.getElementById('rag-btn');
    this.closeRagBtn = document.getElementById('close-rag-btn');
    this.ragSourcesList = document.getElementById('rag-sources-list');
    this.clearRagBtn = document.getElementById('clear-rag-btn');

    // Header Actions
    this.exportChatBtn = document.getElementById('export-chat-btn');
    this.exportDropdown = document.getElementById('export-dropdown');
    this.clearChatBtn = document.getElementById('clear-chat-btn');

    // Status Badges
    this.activeModelBadge = document.getElementById('active-model-badge');
    this.ragCountBadge = document.getElementById('rag-count-badge');
    this.toolsCountBadge = document.getElementById('tools-count-badge');

    // Authentication Elements
    this.authOverlay = document.getElementById('auth-overlay');
    this.authForm = document.getElementById('auth-form');
    this.authEmail = document.getElementById('auth-email');
    this.authPassword = document.getElementById('auth-password');
    this.authTabLogin = document.getElementById('auth-tab-login');
    this.authTabRegister = document.getElementById('auth-tab-register');
    this.authSubmitBtn = document.getElementById('auth-submit-btn');
    this.authSubmitText = document.getElementById('auth-submit-text');
    this.authSpinner = document.getElementById('auth-spinner');
    this.authError = document.getElementById('auth-error');
    this.authGuestBtn = document.getElementById('auth-guest-btn');

    // User Profile in Sidebar
    this.userProfileSection = document.getElementById('user-profile-section');
    this.currentUserEmail = document.getElementById('current-user-email');
    this.userAvatarInitial = document.getElementById('user-avatar-initial');
    this.logoutBtn = document.getElementById('logout-btn');
  }

  // --- Authentication System ---

  async initAuth() {
    // Bind Tab Switching
    if (this.authTabLogin && this.authTabRegister) {
      this.authTabLogin.onclick = () => this.setAuthMode('login');
      this.authTabRegister.onclick = () => this.setAuthMode('register');
    }

    // Bind Auth Form Submit
    if (this.authForm) {
      this.authForm.onsubmit = (e) => this.handleAuthSubmit(e);
    }

    // Bind 1-Click Guest Access
    if (this.authGuestBtn) {
      this.authGuestBtn.onclick = () => this.handleGuestAuth();
    }

    // Bind Logout
    if (this.logoutBtn) {
      this.logoutBtn.onclick = () => this.logout();
    }

    // Check existing token
    if (this.authToken) {
      try {
        const res = await fetch('/api/auth/me', {
          headers: { 'Authorization': `Bearer ${this.authToken}` }
        });
        if (res.ok) {
          const data = await res.json();
          this.currentUser = data.user;
          this.showApp();
          return;
        }
      } catch (e) {
        console.warn('Auth token verification failed', e);
      }
    }

    // If no valid auth, lock application behind auth gate
    this.showAuthOverlay();
  }

  setAuthMode(mode) {
    this.authMode = mode;
    this.hideAuthError();
    if (mode === 'login') {
      this.authTabLogin.classList.add('active');
      this.authTabRegister.classList.remove('active');
      this.authSubmitText.textContent = 'Sign In';
      this.authPassword.autocomplete = 'current-password';
    } else {
      this.authTabRegister.classList.add('active');
      this.authTabLogin.classList.remove('active');
      this.authSubmitText.textContent = 'Create Account';
      this.authPassword.autocomplete = 'new-password';
    }
  }

  showAuthError(message) {
    if (this.authError) {
      this.authError.textContent = message;
      this.authError.style.display = 'block';
    }
  }

  hideAuthError() {
    if (this.authError) {
      this.authError.style.display = 'none';
      this.authError.textContent = '';
    }
  }

  async handleAuthSubmit(e) {
    e.preventDefault();
    this.hideAuthError();

    const email = this.authEmail.value.trim();
    const password = this.authPassword.value;

    if (!email || !password) {
      this.showAuthError('Please fill in all required fields.');
      return;
    }

    // Show loading state
    this.authSubmitBtn.disabled = true;
    this.authSpinner.style.display = 'block';
    this.authSubmitText.style.display = 'none';

    const endpoint = this.authMode === 'register' ? '/api/auth/register' : '/api/auth/login';

    try {
      const res = await fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password })
      });

      const data = await res.json();

      if (!res.ok) {
        throw new Error(data.detail || 'Authentication failed. Please check your credentials.');
      }

      // Success: Save token & state
      this.authToken = data.token;
      this.currentUser = data.user;
      localStorage.setItem('nexus_auth_token', this.authToken);

      this.showApp();
    } catch (err) {
      this.showAuthError(err.message);
    } finally {
      this.authSubmitBtn.disabled = false;
      this.authSpinner.style.display = 'none';
      this.authSubmitText.style.display = 'inline';
    }
  }

  async handleGuestAuth() {
    this.hideAuthError();
    const guestEmail = 'guest@nexus.ai';
    const guestPass = 'nexus_guest_pass_123';

    if (this.authGuestBtn) {
      this.authGuestBtn.disabled = true;
      this.authGuestBtn.textContent = 'Connecting...';
    }

    try {
      // Try login first
      let res = await fetch('/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: guestEmail, password: guestPass })
      });

      // If account does not exist, auto-register
      if (!res.ok) {
        res = await fetch('/api/auth/register', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ email: guestEmail, password: guestPass })
        });
      }

      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || 'Guest access failed');
      }

      this.authToken = data.token;
      this.currentUser = data.user;
      localStorage.setItem('nexus_auth_token', this.authToken);
      this.showApp();
    } catch (err) {
      this.showAuthError('Guest access error: ' + err.message);
    } finally {
      if (this.authGuestBtn) {
        this.authGuestBtn.disabled = false;
        this.authGuestBtn.textContent = '⚡ 1-Click Local Guest Access';
      }
    }
  }

  showAuthOverlay() {
    if (this.authOverlay) {
      this.authOverlay.style.display = 'flex';
    }
    if (this.userProfileSection) {
      this.userProfileSection.style.display = 'none';
    }
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
    this.chatMessages.innerHTML = '';
  }

  showApp() {
    if (this.authOverlay) {
      this.authOverlay.style.display = 'none';
    }
    if (this.userProfileSection) {
      this.userProfileSection.style.display = 'flex';
      this.currentUserEmail.textContent = this.currentUser.email;
      this.userAvatarInitial.textContent = this.currentUser.email.charAt(0).toUpperCase();
    }

    // Initialize application features now that user is authenticated
    this.initWebSocket();
    this.loadSessions();
    this.loadSystemStatus();
  }

  async logout() {
    if (this.authToken) {
      try {
        await fetch('/api/auth/logout', {
          method: 'POST',
          headers: { 'Authorization': `Bearer ${this.authToken}` }
        });
      } catch (e) {
        console.warn('Logout error', e);
      }
    }

    this.authToken = null;
    this.currentUser = null;
    localStorage.removeItem('nexus_auth_token');
    this.sessionId = null;
    this.sessionsList.innerHTML = '';
    this.showAuthOverlay();
  }

  // Authenticated fetch helper
  async authFetch(url, options = {}) {
    const headers = options.headers ? { ...options.headers } : {};
    if (this.authToken) {
      headers['Authorization'] = `Bearer ${this.authToken}`;
    }
    const res = await fetch(url, { ...options, headers });
    if (res.status === 401) {
      this.logout();
      throw new Error('Session expired. Please sign in again.');
    }
    return res;
  }

  // --- WebSocket Connection ---

  initWebSocket() {
    if (this.ws) {
      this.ws.close();
    }
    if (!this.authToken) return;

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws/chat?token=${encodeURIComponent(this.authToken)}`;

    this.ws = new WebSocket(wsUrl);

    this.ws.onopen = () => {
      console.log('Connected to Nexus-AI WebSocket server (Authenticated).');
    };

    this.ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      this.handleStreamEvent(data);
    };

    this.ws.onerror = (err) => {
      console.error('WebSocket Error:', err);
    };

    this.ws.onclose = () => {
      console.log('WebSocket closed.');
    };
  }

  // --- Speech Recognition & TTS ---

  initSpeech() {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (SpeechRecognition) {
      this.recognition = new SpeechRecognition();
      this.recognition.continuous = false;
      this.recognition.interimResults = false;
      this.recognition.lang = 'en-US';

      this.recognition.onstart = () => {
        this.isListening = true;
        this.micBtn.classList.add('active');
      };

      this.recognition.onresult = (e) => {
        const transcript = e.results[0][0].transcript;
        this.userInput.value = transcript;
        this.autoGrowInput();
      };

      this.recognition.onend = () => {
        this.isListening = false;
        this.micBtn.classList.remove('active');
      };

      this.recognition.onerror = (e) => {
        console.warn('Speech recognition error:', e.error);
        this.isListening = false;
        this.micBtn.classList.remove('active');
      };
    } else {
      if (this.micBtn) this.micBtn.style.display = 'none';
    }
  }

  toggleSpeechRecognition() {
    if (!this.recognition) return;
    if (this.isListening) {
      this.recognition.stop();
    } else {
      try {
        this.recognition.start();
      } catch (err) {
        console.warn(err);
      }
    }
  }

  speak(text) {
    if (!this.ttsEnabled || !window.speechSynthesis) return;
    window.speechSynthesis.cancel();
    const cleanText = text.replace(/[#*`_~\[\]\(\)]/g, ' ').replace(/\s+/g, ' ').trim();
    const utterance = new SpeechSynthesisUtterance(cleanText.slice(0, 400));
    window.speechSynthesis.speak(utterance);
  }

  bindEvents() {
    if (this.sendBtn) {
      this.sendBtn.addEventListener('click', () => this.sendMessage());
    }

    if (this.userInput) {
      this.userInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
          e.preventDefault();
          this.sendMessage();
        }
      });

      this.userInput.addEventListener('input', () => this.autoGrowInput());
    }

    if (this.newChatBtn) {
      this.newChatBtn.addEventListener('click', () => this.startNewSession());
    }

    if (this.micBtn) {
      this.micBtn.addEventListener('click', () => this.toggleSpeechRecognition());
    }

    if (this.ttsBtn) {
      this.ttsBtn.addEventListener('click', () => {
        this.ttsEnabled = !this.ttsEnabled;
        this.ttsBtn.classList.toggle('active', this.ttsEnabled);
      });
    }

    if (this.uploadBtn) {
      this.uploadBtn.addEventListener('click', () => this.fileInput.click());
    }

    if (this.fileInput) {
      this.fileInput.addEventListener('change', (e) => this.handleFileUpload(e));
    }

    // Export & Clear Conversation
    if (this.exportChatBtn && this.exportDropdown) {
      this.exportChatBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        this.exportDropdown.classList.toggle('show');
      });
      document.addEventListener('click', (e) => {
        if (!this.exportChatBtn.contains(e.target) && !this.exportDropdown.contains(e.target)) {
          this.exportDropdown.classList.remove('show');
        }
      });
    }

    if (this.clearChatBtn) {
      this.clearChatBtn.addEventListener('click', () => this.clearCurrentConversation());
    }

    // Modal Triggers
    if (this.settingsBtn) {
      this.settingsBtn.addEventListener('click', () => this.openSettings());
    }
    if (this.closeSettingsBtn) {
      this.closeSettingsBtn.addEventListener('click', () => this.settingsModal.classList.remove('open'));
    }
    if (this.saveSettingsBtn) {
      this.saveSettingsBtn.addEventListener('click', () => this.saveSettings());
    }

    if (this.ragBtn) {
      this.ragBtn.addEventListener('click', () => this.openRagModal());
    }
    if (this.closeRagBtn) {
      this.closeRagBtn.addEventListener('click', () => this.ragModal.classList.remove('open'));
    }
    if (this.clearRagBtn) {
      this.clearRagBtn.addEventListener('click', () => this.clearRagKnowledge());
    }
  }

  autoGrowInput() {
    this.userInput.style.height = 'auto';
    this.userInput.style.height = Math.min(this.userInput.scrollHeight, 160) + 'px';
  }

  async loadSystemStatus() {
    try {
      const res = await fetch('/api/status');
      const data = await res.json();
      const provider = data.active_provider || 'self_ai';
      if (provider === 'local' || provider === 'self_ai') {
        this.activeModelBadge.textContent = 'SELF-AI (0 API)';
      } else {
        this.activeModelBadge.textContent = provider.toUpperCase();
      }
      this.toolsCountBadge.textContent = `${data.total_tools} Tools`;
      this.ragCountBadge.textContent = `${data.rag_documents} Docs`;
    } catch (e) {
      console.warn('Failed to load system status', e);
    }
  }

  // --- Session Management ---

  async loadSessions() {
    if (!this.authToken) return;
    try {
      const res = await this.authFetch('/api/sessions');
      const data = await res.json();
      this.sessionsList.innerHTML = '';

      if (data.sessions.length === 0) {
        this.startNewSession();
        return;
      }

      data.sessions.forEach((s) => {
        this.renderSessionItem(s);
      });

      if (!this.sessionId && !this.isGenerating && data.sessions.length > 0) {
        this.switchSession(data.sessions[0].id);
      }
    } catch (e) {
      console.error('Failed to load sessions', e);
    }
  }

  renderSessionItem(session) {
    const item = document.createElement('div');
    item.className = `session-item ${session.id === this.sessionId ? 'active' : ''}`;
    item.dataset.id = session.id;

    const title = document.createElement('span');
    title.className = 'session-title';
    title.textContent = session.title || 'New Conversation';

    const delBtn = document.createElement('button');
    delBtn.className = 'session-delete';
    delBtn.innerHTML = '✕';
    delBtn.title = 'Delete session';
    delBtn.onclick = (e) => {
      e.stopPropagation();
      this.deleteSession(session.id);
    };

    item.appendChild(title);
    item.appendChild(delBtn);

    item.onclick = () => this.switchSession(session.id);
    this.sessionsList.appendChild(item);
  }

  async startNewSession() {
    if (!this.authToken) return;
    try {
      const res = await this.authFetch('/api/sessions', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ title: 'New Conversation' })
      });
      const data = await res.json();
      this.sessionId = data.session_id;
      this.chatMessages.innerHTML = '';
      this.showWelcomeHero();
      await this.loadSessions();
    } catch (e) {
      console.error('Failed to create new session', e);
    }
  }

  async switchSession(sessionId) {
    if (this.sessionId === sessionId || !this.authToken || this.isGenerating) return;
    this.sessionId = sessionId;

    document.querySelectorAll('.session-item').forEach((el) => {
      el.classList.toggle('active', el.dataset.id === sessionId);
    });

    try {
      const res = await this.authFetch(`/api/sessions/${sessionId}`);
      const data = await res.json();
      this.chatMessages.innerHTML = '';

      if (data.messages.length === 0) {
        this.showWelcomeHero();
      } else {
        data.messages.forEach((m) => {
          this.renderHistoricalMessage(m);
        });
      }
      this.scrollToBottom();
    } catch (e) {
      console.error('Failed to load session history', e);
    }
  }

  async deleteSession(sessionId) {
    if (!this.authToken) return;
    try {
      await this.authFetch(`/api/sessions/${sessionId}`, { method: 'DELETE' });
      if (this.sessionId === sessionId) {
        this.sessionId = null;
      }
      await this.loadSessions();
    } catch (e) {
      console.error('Failed to delete session', e);
    }
  }

  showWelcomeHero() {
    this.chatMessages.innerHTML = `
      <div class="welcome-hero">
        <div class="welcome-logo">
          <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="2">
            <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/>
          </svg>
        </div>
        <h1>Nexus-AI Autonomous Platform</h1>
        <p>Your self-contained multimodal AI platform with live ReAct reasoning, Python sandbox, system diagnostics, live weather, web search, calculator, and document knowledge memory.</p>
        <div class="suggestion-grid">
          <div class="suggestion-chip" onclick="app.sendPreset('Check current system status, CPU specs, and available disk space')">
            <strong>🖥️ System Diagnostics</strong>
            <span>Check CPU, OS & disk space</span>
          </div>
          <div class="suggestion-chip" onclick="app.sendPreset('What is the live weather in Tokyo right now?')">
            <strong>🌤️ Global Weather</strong>
            <span>Check live temperature & forecast</span>
          </div>
          <div class="suggestion-chip" onclick="app.sendPreset('Run python code to find the first 15 Fibonacci numbers')">
            <strong>🐍 Python Sandbox</strong>
            <span>Execute Python dynamically</span>
          </div>
          <div class="suggestion-chip" onclick="app.sendPreset('Compute sqrt(144) + 2**8 * 3')">
            <strong>🧮 Fast Math Calculation</strong>
            <span>Evaluate scientific expressions</span>
          </div>
          <div class="suggestion-chip" onclick="app.sendPreset('List the files and directories in the workspace')">
            <strong>📁 Inspect Workspace</strong>
            <span>Show files in project directory</span>
          </div>
          <div class="suggestion-chip" onclick="app.sendPreset('Search web for latest advancements in quantum computing')">
            <strong>🌐 Web Search</strong>
            <span>Look up live news & tech</span>
          </div>
        </div>
      </div>
    `;
  }

  sendPreset(text) {
    this.userInput.value = text;
    this.sendMessage();
  }

  sendMessage() {
    if (!this.authToken) {
      this.showAuthOverlay();
      return;
    }

    const text = this.userInput.value.trim();
    if (!text || this.isGenerating) return;

    // Clear welcome hero if present
    const hero = this.chatMessages.querySelector('.welcome-hero');
    if (hero) hero.remove();

    // Render user message
    this.renderUserMessage(text);
    this.userInput.value = '';
    this.userInput.style.height = 'auto';

    // Start assistant message container
    this.createAssistantMessagePlaceholder();

    this.isGenerating = true;
    this.sendBtn.disabled = true;

    // Send via WebSocket with retry connection polling
    const payload = {
      session_id: this.sessionId,
      message: text
    };

    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(payload));
    } else {
      this.initWebSocket();
      let attempts = 0;
      const poll = setInterval(() => {
        attempts++;
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
          clearInterval(poll);
          this.ws.send(JSON.stringify(payload));
        } else if (attempts >= 30) { // 3 seconds timeout
          clearInterval(poll);
          this.handleStreamEvent({
            type: 'error',
            data: 'Connection to Nexus-AI server timed out. Please check that the server is running.'
          });
        }
      }, 100);
    }
  }

  renderUserMessage(text) {
    const msgEl = document.createElement('div');
    msgEl.className = 'message user';
    msgEl.innerHTML = `
      <div class="message-avatar">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="2">
          <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/>
        </svg>
      </div>
      <div class="message-body">
        <div class="message-author">You</div>
        <div class="message-content">${this.escapeHtml(text)}</div>
      </div>
    `;
    this.chatMessages.appendChild(msgEl);
    this.scrollToBottom();
  }

  createAssistantMessagePlaceholder() {
    const msgEl = document.createElement('div');
    msgEl.className = 'message assistant';
    msgEl.innerHTML = `
      <div class="message-avatar">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="2">
          <polygon points="12 2 2 7 12 12 22 7 12 2"></polygon>
          <polyline points="2 17 12 22 22 17"></polyline>
          <polyline points="2 12 12 17 22 12"></polyline>
        </svg>
      </div>
      <div class="message-body">
        <div class="message-author">NEXUS // ASSISTANT</div>
        <div class="thought-container" style="display: none;">
          <div class="thought-header" onclick="this.parentElement.classList.toggle('open')">
            <span class="thought-title">🧠 Agent Thoughts</span>
            <span class="thought-toggle">▼</span>
          </div>
          <div class="thought-body"></div>
        </div>
        <div class="tools-execution-container"></div>
        <div class="message-content"><span class="typing-cursor">▋</span></div>
      </div>
    `;
    this.chatMessages.appendChild(msgEl);

    this.currentAssistantMessageEl = msgEl;
    this.currentThoughtEl = msgEl.querySelector('.thought-body');
    this.currentContentEl = msgEl.querySelector('.message-content');
    this.currentContentText = '';
    this.currentThoughtText = '';
    this.scrollToBottom();
  }

  renderHistoricalMessage(m) {
    const msgEl = document.createElement('div');
    msgEl.className = `message ${m.role}`;

    if (m.role === 'user') {
      msgEl.innerHTML = `
        <div class="message-avatar">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="2">
            <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/>
          </svg>
        </div>
        <div class="message-body">
          <div class="message-author">You</div>
          <div class="message-content">${this.escapeHtml(m.content)}</div>
        </div>
      `;
    } else {
      let thoughtHtml = '';
      if (m.thoughts) {
        thoughtHtml = `
          <div class="thought-container">
            <div class="thought-header" onclick="this.parentElement.classList.toggle('open')">
              <span class="thought-title">🧠 Agent Thoughts</span>
              <span class="thought-toggle">▼</span>
            </div>
            <div class="thought-body">${this.renderMarkdown(m.thoughts)}</div>
          </div>
        `;
      }
      msgEl.innerHTML = `
        <div class="message-avatar">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="2">
            <polygon points="12 2 2 7 12 12 22 7 12 2"></polygon>
            <polyline points="2 17 12 22 22 17"></polyline>
            <polyline points="2 12 12 17 22 12"></polyline>
          </svg>
        </div>
        <div class="message-body">
          <div class="message-author">NEXUS // ASSISTANT</div>
          ${thoughtHtml}
          <div class="message-content">${this.renderMarkdown(m.content)}</div>
        </div>
      `;
    }
    this.chatMessages.appendChild(msgEl);
  }

  handleStreamEvent(event) {
    if (!this.currentAssistantMessageEl) return;

    switch (event.type) {
      case 'session_created':
        this.sessionId = event.session_id;
        // Do not reload or switch sessions while active streaming is underway
        break;

      case 'thought':
        this.currentThoughtText = (this.currentThoughtText || '') + (this.currentThoughtText ? '\n\n' : '') + event.data;
        const thoughtContainer = this.currentAssistantMessageEl.querySelector('.thought-container');
        if (thoughtContainer) thoughtContainer.style.display = 'block';
        if (this.currentThoughtEl) this.currentThoughtEl.innerHTML = this.renderMarkdown(this.currentThoughtText);
        this.scrollToBottom();
        break;

      case 'tool_start':
        const toolsContainer = this.currentAssistantMessageEl.querySelector('.tools-execution-container');
        if (toolsContainer) {
          const badge = document.createElement('div');
          badge.className = 'tool-badge';
          badge.id = `tool-${event.name}`;
          badge.innerHTML = `⚙️ Executing tool: <strong>${event.name}</strong>...`;
          toolsContainer.appendChild(badge);
          this.scrollToBottom();
        }
        break;

      case 'tool_end':
        const toolBadge = this.currentAssistantMessageEl.querySelector(`#tool-${event.name}`);
        if (toolBadge) {
          toolBadge.innerHTML = `✅ Tool <strong>${event.name}</strong> completed`;
          toolBadge.style.color = '#10b981';
        }
        break;

      case 'token':
        this.currentContentText = (this.currentContentText || '') + event.data;
        const cursor = this.currentContentEl.querySelector('.typing-cursor');
        if (cursor) cursor.remove();
        this.currentContentEl.innerHTML = this.renderMarkdown(this.currentContentText) + '<span class="typing-cursor">▋</span>';
        this.scrollToBottom();
        break;

      case 'done':
        const finalCursor = this.currentContentEl.querySelector('.typing-cursor');
        if (finalCursor) finalCursor.remove();
        if (this.currentContentText) {
          this.currentContentEl.innerHTML = this.renderMarkdown(this.currentContentText);
        }
        this.isGenerating = false;
        this.sendBtn.disabled = false;
        this.loadSessions();
        if (this.ttsEnabled) {
          const rawAssistantText = this.currentContentEl.innerText;
          this.speak(rawAssistantText);
        }
        break;

      case 'error':
        const errCursor = this.currentContentEl.querySelector('.typing-cursor');
        if (errCursor) errCursor.remove();
        this.currentContentEl.innerHTML += `<div style="color: var(--accent-rose); margin-top: 8px;">[Error]: ${this.escapeHtml(event.data)}</div>`;
        this.isGenerating = false;
        this.sendBtn.disabled = false;
        break;
    }
  }

  // --- Document Upload & RAG ---

  async handleFileUpload(e) {
    if (!this.authToken) return;
    const file = e.target.files[0];
    if (!file) return;

    const formData = new FormData();
    formData.append('file', file);

    const originalText = this.uploadBtn.innerHTML;
    this.uploadBtn.innerHTML = '⏳';
    this.uploadBtn.disabled = true;

    try {
      const res = await this.authFetch('/api/upload', {
        method: 'POST',
        body: formData
      });
      const data = await res.json();
      if (res.ok) {
        alert(data.message);
        this.loadSystemStatus();
      } else {
        alert(data.detail || 'Upload failed');
      }
    } catch (err) {
      alert('Upload error: ' + err.message);
    } finally {
      this.uploadBtn.innerHTML = originalText;
      this.uploadBtn.disabled = false;
      this.fileInput.value = '';
    }
  }

  // --- Settings Modal ---

  async openSettings() {
    if (!this.authToken) return;
    try {
      const res = await this.authFetch('/api/config');
      const data = await res.json();
      const cfg = data.raw;

      document.getElementById('setting-provider').value = cfg.active_provider || 'local';
      document.getElementById('setting-gemini-key').value = cfg.gemini_api_key || '';
      document.getElementById('setting-openai-key').value = cfg.openai_api_key || '';
      document.getElementById('setting-groq-key').value = cfg.groq_api_key || '';
      document.getElementById('setting-ollama-url').value = cfg.ollama_base_url || 'http://localhost:11434';
      document.getElementById('setting-temperature').value = cfg.temperature || 0.7;
      document.getElementById('setting-persona').value = cfg.system_persona || '';

      this.settingsModal.classList.add('open');
    } catch (e) {
      console.error(e);
    }
  }

  async saveSettings() {
    if (!this.authToken) return;
    const payload = {
      active_provider: document.getElementById('setting-provider').value,
      gemini_api_key: document.getElementById('setting-gemini-key').value,
      openai_api_key: document.getElementById('setting-openai-key').value,
      groq_api_key: document.getElementById('setting-groq-key').value,
      ollama_base_url: document.getElementById('setting-ollama-url').value,
      temperature: parseFloat(document.getElementById('setting-temperature').value),
      system_persona: document.getElementById('setting-persona').value,
      gemini_model: "gemini-2.0-flash",
      openai_model: "gpt-4o-mini",
      groq_model: "llama-3.3-70b-versatile",
      ollama_model: "llama3",
      enabled_tools: ["code_runner", "web_search", "file_manager", "calculator"]
    };

    try {
      const res = await this.authFetch('/api/config', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      if (res.ok) {
        this.settingsModal.classList.remove('open');
        this.loadSystemStatus();
      }
    } catch (e) {
      alert('Error saving configuration: ' + e.message);
    }
  }

  async openRagModal() {
    if (!this.authToken) return;
    try {
      const res = await this.authFetch('/api/rag/sources');
      const data = await res.json();
      this.ragSourcesList.innerHTML = '';

      if (data.sources.length === 0) {
        this.ragSourcesList.innerHTML = '<div style="color: var(--text-dim); font-size: 13px;">No documents indexed yet. Use the paperclip button to upload files.</div>';
      } else {
        data.sources.forEach((s) => {
          const row = document.createElement('div');
          row.style.cssText = 'display: flex; justify-content: space-between; padding: 8px 12px; background: var(--bg-card); border-radius: 6px; font-size: 13px;';
          row.innerHTML = `<span>📄 <strong>${this.escapeHtml(s.filename)}</strong></span> <span style="color: var(--text-muted);">${s.chunks} chunks</span>`;
          this.ragSourcesList.appendChild(row);
        });
      }

      this.ragModal.classList.add('open');
    } catch (e) {
      console.error(e);
    }
  }

  async clearRagKnowledge() {
    if (!this.authToken) return;
    if (!confirm('Are you sure you want to clear all indexed knowledge documents?')) return;
    try {
      await this.authFetch('/api/rag/clear', { method: 'DELETE' });
      this.openRagModal();
      this.loadSystemStatus();
    } catch (e) {
      alert(e.message);
    }
  }

  scrollToBottom() {
    this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
  }

  escapeHtml(str) {
    if (!str) return '';
    return str
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
  }

  copyCode(btn) {
    const wrapper = btn.closest('.code-block-wrapper');
    if (!wrapper) return;
    const codeEl = wrapper.querySelector('pre code');
    if (!codeEl) return;
    const text = codeEl.innerText;
    navigator.clipboard.writeText(text).then(() => {
      const originalText = btn.innerHTML;
      btn.innerHTML = 'Copied! ✅';
      btn.classList.add('copied');
      setTimeout(() => {
        btn.innerHTML = originalText;
        btn.classList.remove('copied');
      }, 2000);
    }).catch((err) => {
      console.warn('Clipboard copy failed:', err);
    });
  }

  async exportConversation(format) {
    if (this.exportDropdown) {
      this.exportDropdown.classList.remove('show');
    }
    if (!this.sessionId) {
      alert('No active conversation to export.');
      return;
    }

    try {
      const res = await this.authFetch(`/api/sessions/${this.sessionId}`);
      const data = await res.json();
      const messages = data.messages || [];

      if (messages.length === 0) {
        alert('Conversation is empty.');
        return;
      }

      let blob;
      let filename;
      const dateStr = new Date().toISOString().slice(0, 10);

      if (format === 'json') {
        const jsonStr = JSON.stringify({
          session_id: this.sessionId,
          exported_at: new Date().toISOString(),
          messages: messages
        }, null, 2);
        blob = new Blob([jsonStr], { type: 'application/json' });
        filename = `nexus_chat_${dateStr}.json`;
      } else {
        let md = `# Nexus-AI Conversation Export\n\n`;
        md += `*Exported on: ${new Date().toLocaleString()}*\n\n---\n\n`;
        messages.forEach((m) => {
          const author = m.role === 'user' ? '👤 User' : '🤖 Nexus-AI';
          md += `### ${author}\n\n`;
          if (m.thoughts) {
            md += `> **Agent Thoughts**:\n> ${m.thoughts.replace(/\n/g, '\n> ')}\n\n`;
          }
          md += `${m.content}\n\n---\n\n`;
        });
        blob = new Blob([md], { type: 'text/markdown' });
        filename = `nexus_chat_${dateStr}.md`;
      }

      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (e) {
      alert('Failed to export conversation: ' + e.message);
    }
  }

  async clearCurrentConversation() {
    if (!confirm('Are you sure you want to clear this conversation?')) return;
    this.chatMessages.innerHTML = '';
    this.showWelcomeHero();
    if (this.sessionId) {
      await this.deleteSession(this.sessionId);
    }
    await this.startNewSession();
  }

  renderMarkdown(text) {
    if (!text) return '';
    let html = text;

    // Code blocks with syntax copy button and language header
    html = html.replace(/```([a-zA-Z0-9_-]*)\n([\s\S]*?)```/g, (match, lang, code) => {
      const safeLang = (lang || 'code').toLowerCase();
      const safeCode = this.escapeHtml(code.trim());
      return `
        <div class="code-block-wrapper">
          <div class="code-block-header">
            <span class="code-lang">${safeLang}</span>
            <button type="button" class="copy-code-btn" onclick="app.copyCode(this)">📋 Copy</button>
          </div>
          <pre><code class="language-${safeLang}">${safeCode}</code></pre>
        </div>
      `;
    });

    // Inline code
    html = html.replace(/`([^`]+)`/g, (m, c) => `<code>${this.escapeHtml(c)}</code>`);

    // Markdown Links
    html = html.replace(/\[([^\]]+)\]\((https?:\/\/[^\s\)]+)\)/g, '<a href="$2" target="_blank" rel="noopener noreferrer">$1</a>');

    // Headers
    html = html.replace(/^### (.*$)/gim, '<h3>$1</h3>');
    html = html.replace(/^## (.*$)/gim, '<h2>$1</h2>');
    html = html.replace(/^# (.*$)/gim, '<h1>$1</h1>');

    // Blockquotes
    html = html.replace(/^\> (.*$)/gim, '<blockquote>$1</blockquote>');

    // Bold & Italic
    html = html.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
    html = html.replace(/\*([^*]+)\*/g, '<em>$1</em>');

    // Unordered lists
    html = html.replace(/^\s*-\s+(.*$)/gim, '<li>$1</li>');
    html = html.replace(/(<li>.*<\/li>)/s, '<ul>$1</ul>');

    // Line breaks
    html = html.replace(/\n\n/g, '<br/><br/>');

    return html;
  }
}

// Global instance
window.app = new NexusApp();
