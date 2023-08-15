import { MigrationInterface, QueryRunner } from 'typeorm';

export class AddCreatedTimeToUserProcess1606156394891 implements MigrationInterface {
  public async up(queryRunner: QueryRunner): Promise<void> {
    await queryRunner.query(`ALTER TABLE users_processes ADD COLUMN create_time TIMESTAMP NOT NULL DEFAULT CURRENT_DATE`);
  }

  public async down(queryRunner: QueryRunner): Promise<void> {
    await queryRunner.query(`ALTER TABLE users_processes DROP COLUMN create_time`);
  }
}
