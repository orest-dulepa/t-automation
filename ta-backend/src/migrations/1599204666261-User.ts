import { MigrationInterface, QueryRunner } from 'typeorm';

export class User1599204666261 implements MigrationInterface {
  public async up(queryRunner: QueryRunner): Promise<void> {
    await queryRunner.query(
      `CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY NOT NULL,
        email text NOT NULL UNIQUE,
        first_name text NOT NULL,
        last_name text NOT NULL,
        company_id int NOT NULL,
        FOREIGN KEY (company_id) REFERENCES companies (id),
        otp text)`,
    );
  }

  public async down(queryRunner: QueryRunner): Promise<void> {
    await queryRunner.query('DROP TABLE IF EXISTS users');
  }
}
