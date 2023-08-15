import { MigrationInterface, QueryRunner } from 'typeorm';

export class Process1599204739981 implements MigrationInterface {
  public async up(queryRunner: QueryRunner): Promise<void> {
    await queryRunner.query(`CREATE TYPE process_type AS ENUM ('robocorp')`);

    await queryRunner.query(
      `CREATE TABLE IF NOT EXISTS processes (
        id SERIAL PRIMARY KEY NOT NULL,
        name text NOT NULL,
        type process_type NOT NULL,
        credentials json NOT NULL,
        properties text[] NOT NULL)`,
    );
  }

  public async down(queryRunner: QueryRunner): Promise<void> {
    await queryRunner.query('DROP TABLE IF EXISTS processes');

    await queryRunner.query('DROP TYPE IF EXISTS process_type');
  }
}
