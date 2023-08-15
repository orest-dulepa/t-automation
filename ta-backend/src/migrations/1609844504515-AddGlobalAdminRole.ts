import { MigrationInterface, QueryRunner } from 'typeorm';

export class AddGlobalAdminRole1609844504515 implements MigrationInterface {
  public async up(queryRunner: QueryRunner): Promise<void> {
    await queryRunner.query(`
        INSERT INTO roles (id, name)
        VALUES (3, 'admin')
    `);
  }

  public async down(queryRunner: QueryRunner): Promise<void> {
    await queryRunner.query(`
        DELETE FROM roles
        WHERE id = 3;
    `);
  }
}
