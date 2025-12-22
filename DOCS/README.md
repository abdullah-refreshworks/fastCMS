# FastCMS Documentation

FastCMS is a headless CMS built with FastAPI and SQLite. It provides dynamic collection management, authentication, and access control through a web-based admin interface and REST API.

## Documentation Index

### Getting Started
- [Installation & Setup](getting-started.md) - Install FastCMS and get up and running
- [Command Line Interface](cli.md) - Manage FastCMS from the terminal

### Core Concepts
- [Collections](collections.md) - Understanding collection types (Base, Auth, View)
- [Records](records.md) - CRUD operations, filtering, sorting, and pagination
- [Field Types](field-types.md) - Available field types and validation

### Features
- [Authentication](authentication.md) - Built-in admin auth and custom auth collections
- [Two-Factor Authentication](two-factor-auth.md) - TOTP-based 2FA with backup codes
- [Email Verification & Password Reset](email-verification.md) - Email workflows
- [OAuth Authentication](oauth.md) - Social login with Google, GitHub, Microsoft
- [API Keys](api-keys.md) - Service-to-service authentication
- [Security Headers](security-headers.md) - HTTP security headers and CSP
- [Access Control Rules](access-control.md) - Controlling who can access what
- [CSV Import/Export](csv-import-export.md) - Bulk data import and export
- [Bulk Operations](bulk-operations.md) - Update and delete multiple records
- [Webhooks](webhooks.md) - Real-time event notifications
- [Real-time Features](realtime.md) - Live queries and presence tracking
- [Backup & Restore](backup-restore.md) - Database backup and disaster recovery
- [System Settings](system-settings.md) - Application configuration

### Plugins
- [Langflow Plugin](langflow-plugin.md) - Visual AI workflow builder powered by Langflow
- [Plugin Development](plugin-development.md) - Creating custom plugins
- [Available Plugins](plugins.md) - Overview of all plugins

### Advanced Topics
- [Advanced Relations](advanced-relations.md) - Many-to-many, polymorphic relations
- [API Reference](api-reference.md) - Complete API documentation

## Quick Links

- [GitHub Repository](https://github.com/yourusername/fastCMS)
- [Issues & Support](https://github.com/yourusername/fastCMS/issues)
- [Interactive API Docs](http://localhost:8000/docs) (when server is running)

## Contributing

Contributions are welcome! Please read the contributing guidelines before submitting pull requests.

## License

MIT License - see LICENSE file for details
