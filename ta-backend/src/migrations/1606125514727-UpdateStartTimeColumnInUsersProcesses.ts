import { MigrationInterface, QueryRunner } from 'typeorm';

export class UpdateStartTimeColumnInUsersProcesses1606125514727 implements MigrationInterface {
  public async up(queryRunner: QueryRunner): Promise<void> {
    await queryRunner.query(`ALTER TABLE users_processes ALTER COLUMN start_time DROP NOT NULL`);
    await queryRunner.query(`ALTER TABLE users_processes ALTER COLUMN start_time DROP DEFAULT`);
  }

  public async down(queryRunner: QueryRunner): Promise<void> {
    await queryRunner.query(`ALTER TABLE users_processes ALTER COLUMN start_time SET DEFAULT CURRENT_DATE`);
    await queryRunner.query(`ALTER TABLE users_processes ALTER COLUMN start_time SET NOT NULL`);
  }
}
