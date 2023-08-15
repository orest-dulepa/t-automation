import axios, { AxiosInstance, AxiosResponse } from 'axios';

abstract class HttpClient {
  protected readonly instance: AxiosInstance;

  public constructor(baseURL: string) {
    this.instance = axios.create({
      baseURL,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    this.initializeResponseInterceptor();
  }

  private initializeResponseInterceptor = () => {
    this.instance.interceptors.response.use(this.handleSuccessResponse);
  };

  private handleSuccessResponse = ({ data }: AxiosResponse) => data;
}

export default HttpClient;
