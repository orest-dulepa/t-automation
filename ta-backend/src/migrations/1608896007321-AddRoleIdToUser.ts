import { MigrationInterface, QueryRunner } from 'typeorm';

export class AddRoleIdToUser1608896007321 implements MigrationInterface {
  public async up(queryRunner: QueryRunner): Promise<void> {
    await queryRunner.query(`
        ALTER TABLE users ADD role_id int NOT NULL DEFAULT 1
      `);

    await queryRunner.query(`
        ALTER TABLE users ADD CONSTRAINT role_id FOREIGN KEY (role_id) REFERENCES roles (id)
      `);
  }

  public async down(queryRunner: QueryRunner): Promise<void> {
    await queryRunner.query(`ALTER TABLE users DROP COLUMN role_id`);
  }
}
