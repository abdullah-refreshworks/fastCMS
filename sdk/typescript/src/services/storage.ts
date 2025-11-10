/**
 * File storage service
 */
import { FastCMS } from '../client';
import { FileMetadata, FileUploadOptions } from '../types';

export class StorageService {
  constructor(private client: FastCMS) {}

  /**
   * Upload a file
   */
  async upload(file: File | Blob, options?: FileUploadOptions): Promise<FileMetadata> {
    const formData = new FormData();
    formData.append('file', file);

    if (options?.collection) formData.append('collection_name', options.collection);
    if (options?.record) formData.append('record_id', options.record);
    if (options?.field) formData.append('field_name', options.field);

    const response = await this.client.getAxios().post('/api/v1/files', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });

    return response.data;
  }

  /**
   * Get file metadata
   */
  async getFile(fileId: string): Promise<FileMetadata> {
    const response = await this.client.getAxios().get(`/api/v1/files/${fileId}`);
    return response.data;
  }

  /**
   * Get file download URL
   */
  getUrl(fileId: string): string {
    return `${this.client.getAxios().defaults.baseURL}/api/v1/files/${fileId}/download`;
  }

  /**
   * Delete a file
   */
  async delete(fileId: string): Promise<void> {
    await this.client.getAxios().delete(`/api/v1/files/${fileId}`);
  }

  /**
   * List files
   */
  async list(options?: {
    collection?: string;
    record?: string;
    page?: number;
    perPage?: number;
  }): Promise<{ items: FileMetadata[]; page: number; perPage: number; totalItems: number }> {
    const params = new URLSearchParams();

    if (options?.collection) params.append('collection_name', options.collection);
    if (options?.record) params.append('record_id', options.record);
    if (options?.page) params.append('page', options.page.toString());
    if (options?.perPage) params.append('per_page', options.perPage.toString());

    const response = await this.client.getAxios().get(`/api/v1/files?${params.toString()}`);
    return response.data;
  }
}
