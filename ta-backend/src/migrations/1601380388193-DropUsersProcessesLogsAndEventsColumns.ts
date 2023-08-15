import { MigrationInterface, QueryRunner } from 'typeorm';

export class DropUsersProccesLogsAndEventsColumns1601380388193 implements MigrationInterface {
  public async up(queryRunner: QueryRunner): Promise<void> {
    await queryRunner.query(`ALTER TABLE users_processes DROP COLUMN events_source`);
    await queryRunner.query(`ALTER TABLE users_processes DROP COLUMN logs_source`);
  }

  public async down(queryRunner: QueryRunner): Promise<void> {
    await queryRunner.query(`ALTER TABLE users_processes ADD events_source text`);
    await queryRunner.query(`ALTER TABLE users_processes ADD logs_source text`);
  }
}
