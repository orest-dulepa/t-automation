import { MigrationInterface, QueryRunner } from 'typeorm';

export class AddColumnsToScheduledProcess1613381163303 implements MigrationInterface {
  public async up(queryRunner: QueryRunner): Promise<void> {
    await queryRunner.query(
      `ALTER TABLE scheduled_processes ADD COLUMN start_time TIMESTAMP NOT NULL`,
    );

    await queryRunner.query(
      `ALTER TABLE scheduled_processes ADD organization_id int NOT NULL`
    );

    await queryRunner.query(
      `ALTER TABLE scheduled_processes ADD CONSTRAINT organization_id FOREIGN KEY (organization_id) REFERENCES organizations (id)`,
    );
  }

  public async down(queryRunner: QueryRunner): Promise<void> {
    await queryRunner.query(`ALTER TABLE scheduled_processes DROP COLUMN start_time`);
    
    await queryRunner.query(`ALTER TABLE scheduled_processes DROP COLUMN organization_id`);
  }
}
