import {AWS_PROCESS_STATUS} from "@/@types/users-processes";

export type IProcessChangeStatusAWSEvent = {
  detail: {
    status: AWS_PROCESS_STATUS;
    input: string;
  }
  'detail-type': string;
};
