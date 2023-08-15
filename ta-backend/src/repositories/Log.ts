import { AbstractRepository, EntityRepository } from 'typeorm';
import { Log } from '@/entities/Log';
import { UsersProcesses } from '@/entities/UsersProcesses';

@EntityRepository(Log)
export class LogRepository extends AbstractRepository<Log> {
  public insert = (log: Log) => this.repository.save(log);
  public update = (log: Log) => this.repository.save(log);

  public upsert = async (text: string, userProcess: UsersProcesses) => {
    try {
      const existedLog = await this.getByUserProcessId(userProcess.id);

      if (!existedLog) {
        await this.insert(new Log(text, userProcess));
      } else {
        await this.repository
          .createQueryBuilder()
          .update(Log)
          .set({ text })
          .where('userProcess.id = :id', { id: userProcess.id })
          .execute();
      }
    } catch (e) {
      console.log(e);
    }
  };

  public getByUserProcessId = (id: string | number) =>
    this.repository
        .createQueryBuilder('logs')
        .where('logs.userProcess.id = :id', { id })
        .getOne();
}
