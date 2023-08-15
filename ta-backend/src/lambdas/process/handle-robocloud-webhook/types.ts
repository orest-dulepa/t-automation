// https://robocorp.com/docs/robocorp-cloud/webhooks#robot-run-event-structure

export enum EventsTypes {
  processRun = 'process_run',
  robotRunEvent = 'robot_run_event',
}
export interface IProcessRunEvent {
  id: string;
  webhookEventTimestamp: string;
  action: string;
  event: EventsTypes.processRun;
  payload: {
    workspaceId: string;
    processId: string;
    processRunId: string;

    state: 'IP' | 'COMPL';
    duration?: number;
    result?: 'success' | 'error';
    errorCode?: string;
  };
}

export interface IRobotRunEvent {
  id: string;
  webhookEventTimestamp: string;
  action: string;
  event: EventsTypes.robotRunEvent;
  payload: {
    workspaceId: string;
    processId: string;
    processRunId: string;

    robotRunId: string;
    seqNo: number;
    data: object | null;
    timeStamp: string;
    eventType: string;
  };
}

export type IProcessRobocloudWebhookRequest = IProcessRunEvent | IRobotRunEvent;
