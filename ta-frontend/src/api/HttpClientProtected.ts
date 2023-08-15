import { AxiosRequestConfig } from 'axios';

import TokensLocalStorage from '@/local-storage/TokensLocalStorage';

import HttpClient from './HttpClient';

abstract class HttpClientProtected extends HttpClient {
  public constructor(baseURL: string) {
    super(baseURL);

    this.initializeRequestInterceptor();
  }

  private initializeRequestInterceptor = () => {
    this.instance.interceptors.request.use(this.handleRequest);
  };

  private handleRequest = (config: AxiosRequestConfig) => {
    const tokensLocalStorage = TokensLocalStorage.getInstance();

    const accessToken = tokensLocalStorage.getAccessToken();

    const token = `Bearer ${accessToken}`;

    const modifiedConfig = config;

    modifiedConfig.headers.Authorization = token;

    return config;
  };
}

export default HttpClientProtected;
