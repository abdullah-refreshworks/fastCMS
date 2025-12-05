/**
 * FastCMS JavaScript SDK (Lite)
 * A lightweight client for interacting with FastCMS API.
 */

class FastCMS {
    constructor(baseUrl = '/') {
        this.baseUrl = baseUrl.replace(/\/$/, '');
        this.token = localStorage.getItem('fastcms_token') || '';
        this.realtime = new RealtimeClient(this);
    }

    /**
     * Set the authentication token.
     */
    setToken(token) {
        this.token = token;
        localStorage.setItem('fastcms_token', token);
    }

    /**
     * Clear the authentication token.
     */
    clearToken() {
        this.token = '';
        localStorage.removeItem('fastcms_token');
    }

    /**
     * Authenticate with email and password.
     */
    async authWithPassword(email, password) {
        const res = await this.send('/api/v1/auth/login', {
            method: 'POST',
            body: JSON.stringify({ email, password }),
        });
        this.setToken(res.token.access_token);
        return res;
    }

    /**
     * Get a collection reference.
     */
    collection(name) {
        return new Collection(this, name);
    }

    /**
     * Send a request to the API.
     */
    async send(path, options = {}) {
        const headers = {
            'Content-Type': 'application/json',
            ...options.headers,
        };

        if (this.token) {
            headers['Authorization'] = `Bearer ${this.token}`;
        }

        const url = path.startsWith('http') ? path : `${this.baseUrl}${path}`;
        const res = await fetch(url, { ...options, headers });

        if (!res.ok) {
            const err = await res.json().catch(() => ({ message: res.statusText }));
            throw new Error(err.message || res.statusText);
        }

        if (res.status === 204) return null;
        return res.json();
    }
}

class Collection {
    constructor(client, name) {
        this.client = client;
        this.name = name;
    }

    /**
     * List records with optional params.
     * @param {number} page 
     * @param {number} perPage 
     * @param {object} options { filter, sort, expand }
     */
    async getList(page = 1, perPage = 20, options = {}) {
        const params = new URLSearchParams({
            page,
            per_page: perPage,
            ...options
        });
        return this.client.send(`/api/v1/${this.name}/records?${params}`);
    }

    /**
     * Get a single record by ID.
     */
    async getOne(id, options = {}) {
        const params = new URLSearchParams(options);
        return this.client.send(`/api/v1/${this.name}/records/${id}?${params}`);
    }

    /**
     * Create a new record.
     */
    async create(data) {
        return this.client.send(`/api/v1/${this.name}/records`, {
            method: 'POST',
            body: JSON.stringify({ data }),
        });
    }

    /**
     * Update a record.
     */
    async update(id, data) {
        return this.client.send(`/api/v1/${this.name}/records/${id}`, {
            method: 'PATCH',
            body: JSON.stringify({ data }),
        });
    }

    /**
     * Delete a record.
     */
    async delete(id) {
        return this.client.send(`/api/v1/${this.name}/records/${id}`, {
            method: 'DELETE',
        });
    }
    
    /**
     * Subscribe to realtime changes.
     */
    subscribe(callback) {
        return this.client.realtime.subscribe(this.name, callback);
    }
    
    /**
     * Unsubscribe from realtime changes.
     */
    unsubscribe() {
        return this.client.realtime.unsubscribe(this.name);
    }
}

class RealtimeClient {
    constructor(client) {
        this.client = client;
        this.ws = null;
        this.subscriptions = new Map(); // collection -> callback
        this.isConnected = false;
        this.reconnectTimer = null;
    }

    connect() {
        if (this.ws && (this.ws.readyState === WebSocket.OPEN || this.ws.readyState === WebSocket.CONNECTING)) {
            return;
        }

        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const host = this.client.baseUrl.replace(/^http(s)?:\/\//, '') || window.location.host;
        const url = `${protocol}//${host}/ws/realtime`;

        this.ws = new WebSocket(url);

        this.ws.onopen = () => {
            console.log('Realtime connected');
            this.isConnected = true;
            this._authenticate();
        };

        this.ws.onmessage = (event) => {
            try {
                const msg = JSON.parse(event.data);
                this._handleMessage(msg);
            } catch (e) {
                console.error('Failed to parse message', e);
            }
        };

        this.ws.onclose = () => {
            console.log('Realtime disconnected');
            this.isConnected = false;
            this._scheduleReconnect();
        };
    }

    _authenticate() {
        if (this.client.token) {
            this.send({ type: 'auth', token: this.client.token });
        }
        // Resubscribe
        for (const [collection] of this.subscriptions) {
            this.send({ type: 'subscribe', collection });
        }
    }

    _scheduleReconnect() {
        if (this.reconnectTimer) clearTimeout(this.reconnectTimer);
        this.reconnectTimer = setTimeout(() => this.connect(), 3000);
    }

    send(data) {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify(data));
        }
    }

    subscribe(collection, callback) {
        if (!this.isConnected) this.connect();
        this.subscriptions.set(collection, callback);
        this.send({ type: 'subscribe', collection });
        
        return () => this.unsubscribe(collection);
    }

    unsubscribe(collection) {
        this.subscriptions.delete(collection);
        this.send({ type: 'unsubscribe', collection });
    }

    _handleMessage(msg) {
        if (msg.type === 'event') {
            const callback = this.subscriptions.get(msg.collection);
            if (callback) {
                callback(msg);
            }
        }
    }
}

// Export for module usage or global
if (typeof module !== 'undefined') {
    module.exports = FastCMS;
} else {
    window.FastCMS = FastCMS;
}
