import {UsersProcesses} from "@/entities/UsersProcesses";
import {PROCESS_STATUS} from "@/@types/users-processes";

export interface IProcessChangeStatusRequest {
  runId: string;
  newStatus: PROCESS_STATUS;
  isSetEndTimeNeeded?: boolean;
}

export interface IProcessChangeStatusResponse extends Pick<UsersProcesses, 'id'> {}
