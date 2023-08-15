import { MigrationInterface, QueryRunner } from 'typeorm';

export class AddRobocorpRunId1612868410793 implements MigrationInterface {
  public async up(queryRunner: QueryRunner): Promise<void> {
    await queryRunner.query(`ALTER TABLE users_processes ADD robocorp_id int`);
  }

  public async down(queryRunner: QueryRunner): Promise<void> {
    await queryRunner.query(`ALTER TABLE users_processes DROP COLUMN robocorp_id`);
  }
}
