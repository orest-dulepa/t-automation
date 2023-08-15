declare namespace NodeJS {
  export interface ProcessEnv {
    NODE_ENV: 'development' | 'production';
    PORT?: string;
    BASE_URL: string;
  }
}
