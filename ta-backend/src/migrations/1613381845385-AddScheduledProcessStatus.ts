import { MigrationInterface, QueryRunner } from 'typeorm';

export class AddScheduledProcessStatus1613381845385 implements MigrationInterface {
  public async up(queryRunner: QueryRunner): Promise<void> {
    await queryRunner.query(`ALTER TABLE scheduled_processes ALTER COLUMN status DROP DEFAULT`);
    await queryRunner.query(`ALTER TYPE scheduled_process_status_type RENAME TO scheduled_process_status_type_old`);
    await queryRunner.query(`CREATE TYPE scheduled_process_status_type AS ENUM ('scheduled', 'succeeded', 'canceled')`);
    await queryRunner.query(`ALTER TABLE scheduled_processes ALTER COLUMN status TYPE scheduled_process_status_type USING status::text::scheduled_process_status_type`);
    await queryRunner.query(`DROP TYPE scheduled_process_status_type_old`);
    await queryRunner.query(`ALTER TABLE scheduled_processes ALTER COLUMN status SET DEFAULT 'scheduled'`);
  }

  public async down(queryRunner: QueryRunner): Promise<void> {
    await queryRunner.query(`ALTER TABLE scheduled_processes ALTER COLUMN status DROP DEFAULT`);
    await queryRunner.query(`ALTER TYPE scheduled_process_status_type RENAME TO scheduled_process_status_type_old`);
    await queryRunner.query(`CREATE TYPE scheduled_process_status_type AS ENUM ('scheduled', 'canceled')`);
    await queryRunner.query(`ALTER TABLE scheduled_processes ALTER COLUMN status TYPE scheduled_process_status_type USING status::text::scheduled_process_status_type`);
    await queryRunner.query(`DROP TYPE scheduled_process_status_type_old`);
    await queryRunner.query(`ALTER TABLE scheduled_processes ALTER COLUMN status SET DEFAULT 'scheduled'`);
  }
}
