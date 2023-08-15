import { IProcessRunEvent, EventsTypes } from '../types';

import Handler from './Handler';

class ProcessRunEventHandler extends Handler {
  public readonly type = EventsTypes.processRun;

  public constructor() {
    super();
  }

  public execute = async ({ event, payload }: IProcessRunEvent) => {
    console.log(`EXECUTED: ${event} | ${JSON.stringify(payload)}`);
  };
}

export default ProcessRunEventHandler;
