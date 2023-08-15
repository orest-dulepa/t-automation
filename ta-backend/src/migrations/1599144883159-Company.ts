import { MigrationInterface, QueryRunner } from 'typeorm';

export class Company1599144883159 implements MigrationInterface {
  public async up(queryRunner: QueryRunner): Promise<void> {
    await queryRunner.query(
      `CREATE TABLE IF NOT EXISTS companies (
        id SERIAL PRIMARY KEY NOT NULL,
        name text NOT NULL)`,
    );
  }

  public async down(queryRunner: QueryRunner): Promise<void> {
    await queryRunner.query('DROP TABLE IF EXISTS companies');
  }
}
