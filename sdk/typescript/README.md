# FastCMS TypeScript/JavaScript SDK

Official TypeScript/JavaScript SDK for FastCMS - AI-Native Backend-as-a-Service.

## Installation

```bash
npm install fastcms-js
# or
yarn add fastcms-js
```

## Quick Start

```typescript
import { FastCMS } from 'fastcms-js';

// Initialize client
const client = new FastCMS({
  baseUrl: 'http://localhost:8000',
});

// Authentication
await client.auth.signUpWithEmail('user@example.com', 'password');
await client.auth.signInWithEmail('user@example.com', 'password');

// Type-safe collection client
interface Post {
  id: string;
  title: string;
  content: string;
  author: string;
  created: string;
}

const posts = client.collection<Post>('posts');

// CRUD operations
const post = await posts.create({
  title: 'Hello World',
  content: 'My first post',
  author: 'user-id',
});

const list = await posts.getList({
  filter: 'author="user-id"',
  sort: '-created',
  page: 1,
  perPage: 20,
});

const single = await posts.getOne(post.id, {
  expand: 'author',
});

await posts.update(post.id, {
  title: 'Updated Title',
});

await posts.delete(post.id);

// Real-time subscriptions
posts.subscribe((event) => {
  console.log(event.action, event.record);
});

// Full-text search
const results = await client.search.search('posts', 'hello world', {
  limit: 10,
});

// File upload
const file = await client.storage.upload(fileBlob, {
  collection: 'posts',
  record: post.id,
});

const fileUrl = client.storage.getUrl(file.id);
```

## Features

- ✅ Type-safe collection operations
- ✅ Authentication (Email, OAuth, JWT)
- ✅ Real-time subscriptions
- ✅ Full-text search
- ✅ File storage
- ✅ Relations and expansion
- ✅ Advanced filtering
- ✅ Pagination and sorting

## Documentation

Full documentation: https://docs.fastcms.dev

## License

MIT
