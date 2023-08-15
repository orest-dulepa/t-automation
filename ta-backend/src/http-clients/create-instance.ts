import axios, { AxiosResponse, AxiosError } from 'axios';

export const createInstance = (baseURL: string) => {
  const instance = axios.create({
    baseURL,
    headers: {
      'Content-Type': 'application/json',
    },
  });

  const handleSuccess = ({ data }: AxiosResponse) => data;

  const handleError = (error: AxiosError) => Promise.reject(error);

  instance.interceptors.response.use(handleSuccess, handleError);

  return instance;
};
