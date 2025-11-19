/**
 * Authentication service
 */
import { FastCMS } from '../client';
import { User, AuthTokens } from '../types';

export class AuthService {
  constructor(private client: FastCMS) {}

  /**
   * Sign up with email and password
   */
  async signUpWithEmail(email: string, password: string, name?: string): Promise<User> {
    const response = await this.client.getAxios().post('/api/v1/auth/register', {
      email,
      password,
      name,
    });

    return response.data;
  }

  /**
   * Sign in with email and password
   */
  async signInWithEmail(email: string, password: string): Promise<{ user: User; tokens: AuthTokens }> {
    const response = await this.client.getAxios().post('/api/v1/auth/login', {
      email,
      password,
    });

    const tokens = {
      accessToken: response.data.access_token,
      refreshToken: response.data.refresh_token,
    };

    this.client.setTokens(tokens);

    return {
      user: response.data.user,
      tokens,
    };
  }

  /**
   * Sign in with OAuth provider
   */
  async signInWithOAuth(provider: 'google' | 'github' | 'microsoft'): Promise<string> {
    const response = await this.client.getAxios().get(`/api/v1/oauth/login/${provider}`);
    return response.data.auth_url;
  }

  /**
   * Refresh access token
   */
  async refreshToken(refreshToken: string): Promise<AuthTokens> {
    const response = await this.client.getAxios().post('/api/v1/auth/refresh', {
      refresh_token: refreshToken,
    });

    const tokens = {
      accessToken: response.data.access_token,
      refreshToken: response.data.refresh_token,
    };

    this.client.setTokens(tokens);
    return tokens;
  }

  /**
   * Get current user
   */
  async getCurrentUser(): Promise<User> {
    const response = await this.client.getAxios().get('/api/v1/auth/me');
    return response.data;
  }

  /**
   * Update current user
   */
  async updateUser(data: Partial<User>): Promise<User> {
    const response = await this.client.getAxios().patch('/api/v1/auth/me', data);
    return response.data;
  }

  /**
   * Request password reset
   */
  async requestPasswordReset(email: string): Promise<void> {
    await this.client.getAxios().post('/api/v1/auth/request-password-reset', { email });
  }

  /**
   * Reset password with token
   */
  async resetPassword(token: string, newPassword: string): Promise<void> {
    await this.client.getAxios().post('/api/v1/auth/reset-password', {
      token,
      new_password: newPassword,
    });
  }

  /**
   * Change password (authenticated)
   */
  async changePassword(oldPassword: string, newPassword: string): Promise<void> {
    await this.client.getAxios().post('/api/v1/auth/change-password', {
      old_password: oldPassword,
      new_password: newPassword,
    });
  }

  /**
   * Sign out
   */
  signOut(): void {
    this.client.clearAuth();
  }
}
