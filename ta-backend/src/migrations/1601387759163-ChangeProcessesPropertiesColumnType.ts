import { MigrationInterface, QueryRunner } from 'typeorm';

export class ChangeProcessesPropertiesColumnType1601387759163 implements MigrationInterface {
  public async up(queryRunner: QueryRunner): Promise<void> {
    await queryRunner.query(`ALTER TABLE processes DROP COLUMN properties`);
    await queryRunner.query(`ALTER TABLE processes ADD properties json NOT NULL DEFAULT '[]'`);
  }

  public async down(queryRunner: QueryRunner): Promise<void> {
    await queryRunner.query(`ALTER TABLE processes DROP COLUMN properties`);
    await queryRunner.query(`ALTER TABLE processes ADD properties text[] NOT NULL DEFAULT '{}'`);
  }
}
