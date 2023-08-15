import { IProcessRobocloudWebhookRequest, EventsTypes } from '../types';

abstract class Handler {
  abstract readonly type: EventsTypes;
  private next?: Handler;

  public setNext = (next: Handler) => {
    this.next = next;
  };

  public try = async (request: IProcessRobocloudWebhookRequest) => {
    if (request.event === this.type) {
      await this.execute(request);
      return;
    }

    if (this.next) {
      this.next.try(request);
      return;
    }

    console.log(`ERROR: unknown event - ${request.event}`);
  };

  abstract execute(event: IProcessRobocloudWebhookRequest): Promise<void>;
}

export default Handler;
