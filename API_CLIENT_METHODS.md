/**
 * Updated API client methods to match Django backend exactly
 */

// Add these methods to the PromptCraftApiClient class

// Authentication Methods (updated to match Django URLs)
async login(username: string, password: string): Promise<LoginResponse> {
  try {
    const response = await this.axiosInstance.post<LoginResponse>('/auth/login/', {
      username,
      password
    });
    
    const { access, refresh } = response.data;
    this.setTokens(access, refresh);
    this.emit('login', response.data);
    
    return response.data;
  } catch (error) {
    throw this.handleApiError(error as AxiosError);
  }
}

async register(userData: UserRegistrationRequest): Promise<LoginResponse> {
  try {
    const response = await this.axiosInstance.post<LoginResponse>('/auth/register/', userData);
    
    const { access, refresh } = response.data;
    this.setTokens(access, refresh);
    this.emit('login', response.data);
    
    return response.data;
  } catch (error) {
    throw this.handleApiError(error as AxiosError);
  }
}

async getProfile(): Promise<UserProfile> {
  try {
    const response = await this.axiosInstance.get<UserProfile>('/auth/profile/');
    return response.data;
  } catch (error) {
    throw this.handleApiError(error as AxiosError);
  }
}

async updateProfile(data: Partial<UserUpdate>): Promise<UserProfile> {
  try {
    const response = await this.axiosInstance.patch<UserProfile>('/auth/profile/', data);
    return response.data;
  } catch (error) {
    throw this.handleApiError(error as AxiosError);
  }
}

// Template Methods (updated to match Django URLs)
async getTemplates(params?: TemplateQueryParams): Promise<PaginatedResponse<TemplateList>> {
  try {
    const response = await this.axiosInstance.get<PaginatedResponse<TemplateList>>('/templates/', {
      params
    });
    return response.data;
  } catch (error) {
    throw this.handleApiError(error as AxiosError);
  }
}

async getTemplate(id: string): Promise<TemplateDetail> {
  try {
    const response = await this.axiosInstance.get<TemplateDetail>(`/templates/${id}/`);
    return response.data;
  } catch (error) {
    throw this.handleApiError(error as AxiosError);
  }
}

async getFeaturedTemplates(): Promise<TemplateList[]> {
  try {
    const response = await this.axiosInstance.get<TemplateList[]>('/templates/featured/');
    return response.data;
  } catch (error) {
    throw this.handleApiError(error as AxiosError);
  }
}

async getTrendingTemplates(): Promise<TemplateList[]> {
  try {
    const response = await this.axiosInstance.get<TemplateList[]>('/templates/trending/');
    return response.data;
  } catch (error) {
    throw this.handleApiError(error as AxiosError);
  }
}

async getMyTemplates(): Promise<TemplateList[]> {
  try {
    const response = await this.axiosInstance.get<TemplateList[]>('/templates/my_templates/');
    return response.data;
  } catch (error) {
    throw this.handleApiError(error as AxiosError);
  }
}

// Category Methods
async getCategories(params?: CategoryQueryParams): Promise<PaginatedResponse<TemplateCategory>> {
  try {
    const response = await this.axiosInstance.get<PaginatedResponse<TemplateCategory>>('/template-categories/', {
      params
    });
    return response.data;
  } catch (error) {
    throw this.handleApiError(error as AxiosError);
  }
}

// Health Check
async healthCheck(): Promise<HealthStatus> {
  try {
    const response = await this.axiosInstance.get<HealthStatus>('/core/health/');
    return response.data;
  } catch (error) {
    throw this.handleApiError(error as AxiosError);
  }
}

// Utility Methods
isAuthenticated(): boolean {
  return !!this.accessToken;
}

clearAuth(): void {
  this.clearTokens();
}
