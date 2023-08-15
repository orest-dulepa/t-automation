export enum PROCESS_STATUS {
  ACTIVE = 'active',
  PROCESSING = 'processing',
  FINISHED = 'finished',
  FAILED = 'failed',
  INITIALIZED = 'initialized',
  WARNING = 'warning',
}

export enum AWS_PROCESS_STATUS {
  RUNNING = 'RUNNING',
  SUCCEEDED = 'SUCCEEDED',
  FAILED = 'FAILED',
  TIMED_OUT = 'TIMED_OUT',
  ABORTED = 'ABORTED',
}

export enum AWS_PROCESS_STATUS_TO_STANDART_STATUS {
  RUNNING = 'processing',
  SUCCEEDED = 'finished',
  FAILED = 'failed',
  TIMED_OUT = 'failed',
  ABORTED = 'failed',
}
