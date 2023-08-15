import axios, { AxiosRequestConfig } from 'axios';

declare module 'axios' {
  interface AxiosResponse<T = any> extends Promise<T> {}

  interface AxiosError<T> {
    config: AxiosRequestConfig;
    response: {
      status: number;
      data: T;
    };
    isAxiosError: boolean;
    toJSON: () => object;
  }
}
