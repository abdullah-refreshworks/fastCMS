/**
 * Full-text search service
 */
import { FastCMS } from '../client';
import { SearchOptions, SearchResult } from '../types';

export class SearchService {
  constructor(private client: FastCMS) {}

  /**
   * Perform full-text search on a collection
   */
  async search<T = any>(
    collectionName: string,
    query: string,
    options?: SearchOptions
  ): Promise<SearchResult<T>> {
    const params = new URLSearchParams();
    params.append('q', query);

    if (options?.limit) params.append('limit', options.limit.toString());
    if (options?.offset) params.append('offset', options.offset.toString());

    const response = await this.client.getAxios().get(
      `/api/v1/search/${collectionName}?${params.toString()}`
    );

    return response.data;
  }

  /**
   * Create search index for a collection (admin only)
   */
  async createIndex(collectionName: string, fields: string[]): Promise<void> {
    await this.client.getAxios().post('/api/v1/search/indexes', {
      collection_name: collectionName,
      fields,
    });
  }

  /**
   * Delete search index (admin only)
   */
  async deleteIndex(collectionName: string): Promise<void> {
    await this.client.getAxios().delete(`/api/v1/search/indexes/${collectionName}`);
  }

  /**
   * Reindex a collection (admin only)
   */
  async reindex(collectionName: string): Promise<{ records_indexed: number }> {
    const response = await this.client.getAxios().post(
      `/api/v1/search/indexes/${collectionName}/reindex`
    );
    return response.data;
  }

  /**
   * List all search indexes
   */
  async listIndexes(): Promise<Array<{
    id: string;
    collection_name: string;
    indexed_fields: string[];
  }>> {
    const response = await this.client.getAxios().get('/api/v1/search/indexes');
    return response.data;
  }
}
