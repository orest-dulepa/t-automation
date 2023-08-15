import { AbstractRepository, EntityRepository } from 'typeorm';
import { Event } from '@/entities/Event';

@EntityRepository(Event)
export class EventRepository extends AbstractRepository<Event> {
  public insert = (event: Event) => this.repository.save(event);

  public getAllByUserProcessId = (id: string | number) =>
    this.repository
      .createQueryBuilder('events')
      .where('events.userProcess.id = :id', { id })
      .getMany();
}
