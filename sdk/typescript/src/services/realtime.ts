/**
 * Real-time subscriptions service (SSE)
 */
import { FastCMS } from '../client';
import { RealtimeEvent, UnsubscribeFn } from '../types';

export class RealtimeService {
  private eventSources: Map<string, EventSource> = new Map();

  constructor(private client: FastCMS) {}

  /**
   * Subscribe to real-time updates for a collection
   */
  subscribe<T = any>(
    collectionName: string,
    callback: (event: RealtimeEvent<T>) => void
  ): UnsubscribeFn {
    const tokens = this.client.getTokens();
    const baseUrl = this.client.getAxios().defaults.baseURL;
    const url = `${baseUrl}/api/v1/realtime/${collectionName}${
      tokens?.accessToken ? `?token=${tokens.accessToken}` : ''
    }`;

    const eventSource = new EventSource(url);

    eventSource.onmessage = (e) => {
      try {
        const data = JSON.parse(e.data);
        callback(data);
      } catch (error) {
        console.error('Failed to parse realtime event:', error);
      }
    };

    eventSource.onerror = (error) => {
      console.error('EventSource error:', error);
    };

    const key = `${collectionName}-${Date.now()}`;
    this.eventSources.set(key, eventSource);

    // Return unsubscribe function
    return () => {
      const es = this.eventSources.get(key);
      if (es) {
        es.close();
        this.eventSources.delete(key);
      }
    };
  }

  /**
   * Close all subscriptions
   */
  closeAll(): void {
    this.eventSources.forEach((es) => es.close());
    this.eventSources.clear();
  }
}
