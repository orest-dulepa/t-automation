import { MigrationInterface, QueryRunner } from 'typeorm';

export class AddNewProcessStatus1605868111155 implements MigrationInterface {
  public async up(queryRunner: QueryRunner): Promise<void> {
    await queryRunner.query(`ALTER TABLE users_processes ALTER COLUMN status DROP DEFAULT`);
    await queryRunner.query(`ALTER TYPE status_type RENAME TO status_type_old`);
    await queryRunner.query(`CREATE TYPE status_type AS ENUM ('active', 'processing', 'finished', 'failed', 'initialized')`);
    await queryRunner.query(`ALTER TABLE users_processes ALTER COLUMN status TYPE status_type USING status::text::status_type`);
    await queryRunner.query(`DROP TYPE status_type_old`);
    await queryRunner.query(`ALTER TABLE users_processes ALTER COLUMN status SET DEFAULT 'initialized'`);
  }

  public async down(queryRunner: QueryRunner): Promise<void> {
    await queryRunner.query(`ALTER TABLE users_processes ALTER COLUMN status DROP DEFAULT`);
    await queryRunner.query(`ALTER TYPE status_type RENAME TO status_type_old`);
    await queryRunner.query(`CREATE TYPE status_type AS ENUM ('active', 'processing', 'finished', 'failed')`);
    await queryRunner.query(`ALTER TABLE users_processes ALTER COLUMN status TYPE status_type USING status::text::status_type`);
    await queryRunner.query(`DROP TYPE status_type_old`);
    await queryRunner.query(`ALTER TABLE users_processes ALTER COLUMN status SET DEFAULT 'active'`);
  }
}
