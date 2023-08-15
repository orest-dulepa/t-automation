declare namespace NodeJS {
  export interface ProcessEnv {
    DB_NAME: string;
    DB_USER: string;
    DB_PWD: string;
    DB_HOST: string;
    DB_PORT: string;
    JWT_SECRET: string;
    STAGE: string;
    LOGS_QUEUE_URL: string;
    BUCKET_NAME: string;
  }
}
