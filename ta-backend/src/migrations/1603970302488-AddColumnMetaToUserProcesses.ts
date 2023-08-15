import { MigrationInterface, QueryRunner } from 'typeorm';

export class AddColumnMetaToUserProcesses1603970302488 implements MigrationInterface {
  public async up(queryRunner: QueryRunner): Promise<void> {
    await queryRunner.query(`ALTER TABLE users_processes ADD meta json NOT NULL DEFAULT '[]'`);
  }

  public async down(queryRunner: QueryRunner): Promise<void> {
    await queryRunner.query(`ALTER TABLE users_processes DROP COLUMN meta`);
  }
}
