import { MigrationInterface, QueryRunner } from 'typeorm';

export class ChangeScheduledProcessColumnType21613395374626 implements MigrationInterface {
  public async up(queryRunner: QueryRunner): Promise<void> {
    await queryRunner.query(
      `ALTER TABLE scheduled_processes DROP COLUMN IF EXISTS start_time`
    );

    await queryRunner.query(
      `ALTER TABLE scheduled_processes ADD COLUMN start_time BIGINT`,
    );
  }

  public async down(queryRunner: QueryRunner): Promise<void> {
    await queryRunner.query(
      `ALTER TABLE scheduled_processes DROP COLUMN start_time`
    );

    await queryRunner.query(
      `ALTER TABLE scheduled_processes ADD COLUMN start_time timestamp with time zone`,
    );
  }
}
