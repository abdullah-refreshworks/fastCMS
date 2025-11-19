/**
 * Collection service for CRUD operations
 */
import { FastCMS } from '../client';
import { QueryOptions, ListResult, UnsubscribeFn, RealtimeEvent } from '../types';

export class CollectionClient<T = any> {
  constructor(private client: FastCMS, private collectionName: string) {}

  /**
   * Create a new record
   */
  async create(data: Partial<T>): Promise<T> {
    const response = await this.client.getAxios().post(
      `/api/v1/${this.collectionName}/records`,
      data
    );
    return response.data;
  }

  /**
   * Get list of records
   */
  async getList(options?: QueryOptions): Promise<ListResult<T>> {
    const params = new URLSearchParams();

    if (options?.filter) params.append('filter', options.filter);
    if (options?.sort) params.append('sort', options.sort);
    if (options?.page) params.append('page', options.page.toString());
    if (options?.perPage) params.append('per_page', options.perPage.toString());
    if (options?.expand) params.append('expand', options.expand);

    const response = await this.client.getAxios().get(
      `/api/v1/${this.collectionName}/records?${params.toString()}`
    );

    return response.data;
  }

  /**
   * Get a single record by ID
   */
  async getOne(id: string, options?: { expand?: string }): Promise<T> {
    const params = new URLSearchParams();
    if (options?.expand) params.append('expand', options.expand);

    const response = await this.client.getAxios().get(
      `/api/v1/${this.collectionName}/records/${id}?${params.toString()}`
    );

    return response.data;
  }

  /**
   * Update a record
   */
  async update(id: string, data: Partial<T>): Promise<T> {
    const response = await this.client.getAxios().patch(
      `/api/v1/${this.collectionName}/records/${id}`,
      data
    );
    return response.data;
  }

  /**
   * Delete a record
   */
  async delete(id: string): Promise<void> {
    await this.client.getAxios().delete(
      `/api/v1/${this.collectionName}/records/${id}`
    );
  }

  /**
   * Subscribe to real-time updates
   */
  subscribe(callback: (event: RealtimeEvent<T>) => void): UnsubscribeFn {
    return this.client.realtime.subscribe(this.collectionName, callback);
  }
}
