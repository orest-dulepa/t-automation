import { MigrationInterface, QueryRunner } from 'typeorm';

export class AddProcessTypes1601027086378 implements MigrationInterface {
  public async up(queryRunner: QueryRunner): Promise<void> {
    await queryRunner.query(`
            ALTER TABLE processes ALTER COLUMN type TYPE VARCHAR(255);

            DROP TYPE IF EXISTS process_type CASCADE;

            CREATE TYPE process_type AS ENUM ('robocorp', 'uipath_be1', 'uipath_be2');
        `);

    await queryRunner.query(`
            ALTER TABLE processes ALTER COLUMN type TYPE process_type USING (type::process_type);
        `);
  }

  public async down(queryRunner: QueryRunner): Promise<void> {
    await queryRunner.query(`
            ALTER TABLE processes ALTER COLUMN type TYPE VARCHAR(255);
        `);

    await queryRunner.query(`
            DROP TYPE IF EXISTS process_type CASCADE;
            CREATE TYPE process_type AS ENUM ('robocorp');
        `);

    await queryRunner.query(`
            ALTER TABLE processes ALTER COLUMN type TYPE process_type USING (type::process_type);
        `);
  }
}
