import { MigrationInterface, QueryRunner } from 'typeorm';

export class ChangeScheduledProcessColumnType1613392106487 implements MigrationInterface {
  public async up(queryRunner: QueryRunner): Promise<void> {
    await queryRunner.query(
      `ALTER TABLE scheduled_processes ALTER COLUMN start_time TYPE TIMESTAMP with time zone`,
    );
  }

  public async down(queryRunner: QueryRunner): Promise<void> {
    await queryRunner.query(
      `ALTER TABLE scheduled_processes ALTER COLUMN start_time TYPE TIMESTAMP`,
    );
  }
}
