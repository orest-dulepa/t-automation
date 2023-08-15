import { MigrationInterface, QueryRunner } from 'typeorm';

export class Role1608894674640 implements MigrationInterface {
  public async up(queryRunner: QueryRunner): Promise<void> {
    await queryRunner.query(
      `CREATE TABLE IF NOT EXISTS roles (
          id SERIAL PRIMARY KEY NOT NULL,
          name text NOT NULL UNIQUE)`,
    );

    await queryRunner.query(`
        INSERT INTO roles (id, name)
        VALUES (1, 'employee')
    `);

    await queryRunner.query(`
        INSERT INTO roles (id, name)
        VALUES (2, 'manager')
    `);
  }

  public async down(queryRunner: QueryRunner): Promise<void> {
    await queryRunner.query('DROP TABLE IF EXISTS roles');
  }
}
