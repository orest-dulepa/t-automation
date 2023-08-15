import { UsersProcessesRepository } from '@/repositories/UsersProcesses';
import { EventRepository } from '@/repositories/Event';

import { Event } from '@/entities/Event';

import { IRobotRunEvent, EventsTypes } from '../types';

import Handler from './Handler';

class RobotRunEventHandler extends Handler {
  public readonly type = EventsTypes.robotRunEvent;
  private readonly usersProcessesRepository: UsersProcessesRepository;
  private readonly eventRepository: EventRepository;

  public constructor(
    usersProcessesRepository: UsersProcessesRepository,
    eventRepository: EventRepository,
  ) {
    super();

    this.usersProcessesRepository = usersProcessesRepository;
    this.eventRepository = eventRepository;
  }

  public execute = async ({ payload }: IRobotRunEvent) => {
    const { processRunId, seqNo, timeStamp, eventType } = payload;

    const userProcess = await this.usersProcessesRepository.getByProcessRunId(processRunId);

    if (!userProcess) {
      throw new Error(`ERROR: could not found userProcess by processRunId: ${processRunId}`);
    }

    const eventEntity = new Event(String(seqNo), timeStamp, eventType, userProcess);

    await this.eventRepository.insert(eventEntity);
  };
}

export default RobotRunEventHandler;
