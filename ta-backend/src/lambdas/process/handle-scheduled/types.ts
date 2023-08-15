export type IHandleScheduledProcessRequest = {
  Payload: {
    Input: {
      scheduledProcessId: string | number;
      changeStatusUrl: string;
    };
  };
};
