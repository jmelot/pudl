"""Add my cool lil respondent id glue tables and other 714 xbrl updates

Revision ID: 8fffc1d0399a
Revises: a93bdb8d4fbd
Create Date: 2024-09-24 09:28:45.862748

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '8fffc1d0399a'
down_revision = 'a93bdb8d4fbd'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('core_pudl__assn_ferc714_pudl_respondents',
    sa.Column('respondent_id_ferc714', sa.Integer(), nullable=False, comment='PUDL-assigned identifying a respondent to FERC Form 714. This ID associates natively reported respondent IDs from the orignal CSV and XBRL data sources.'),
    sa.PrimaryKeyConstraint('respondent_id_ferc714', name=op.f('pk_core_pudl__assn_ferc714_pudl_respondents'))
    )
    op.create_table('core_pudl__assn_ferc714_csv_pudl_respondents',
    sa.Column('respondent_id_ferc714', sa.Integer(), nullable=False, comment='PUDL-assigned identifying a respondent to FERC Form 714. This ID associates natively reported respondent IDs from the orignal CSV and XBRL data sources.'),
    sa.Column('respondent_id_ferc714_csv', sa.Integer(), nullable=False, comment='FERC Form 714 respondent ID from CSV reported data - published from years: 2006-2020. This ID is linked to the newer years of reported XBRL data through the PUDL-assigned respondent_id_ferc714 ID. This ID was originally reported as respondent_id. Note that this ID does not correspond to FERC respondent IDs from other forms.'),
    sa.ForeignKeyConstraint(['respondent_id_ferc714'], ['core_pudl__assn_ferc714_pudl_respondents.respondent_id_ferc714'], name=op.f('fk_core_pudl__assn_ferc714_csv_pudl_respondents_respondent_id_ferc714_core_pudl__assn_ferc714_pudl_respondents')),
    sa.PrimaryKeyConstraint('respondent_id_ferc714', 'respondent_id_ferc714_csv', name=op.f('pk_core_pudl__assn_ferc714_csv_pudl_respondents'))
    )
    op.create_table('core_pudl__assn_ferc714_xbrl_pudl_respondents',
    sa.Column('respondent_id_ferc714', sa.Integer(), nullable=False, comment='PUDL-assigned identifying a respondent to FERC Form 714. This ID associates natively reported respondent IDs from the orignal CSV and XBRL data sources.'),
    sa.Column('respondent_id_ferc714_xbrl', sa.Text(), nullable=False, comment='FERC Form 714 respondent ID from XBRL reported data - published from years: 2021-present. This ID is linked to the older years of reported CSV data through the PUDL-assigned respondent_id_ferc714 ID. This ID was originally reported as entity_id. Note that this ID does not correspond to FERC respondent IDs from other forms.'),
    sa.ForeignKeyConstraint(['respondent_id_ferc714'], ['core_pudl__assn_ferc714_pudl_respondents.respondent_id_ferc714'], name=op.f('fk_core_pudl__assn_ferc714_xbrl_pudl_respondents_respondent_id_ferc714_core_pudl__assn_ferc714_pudl_respondents')),
    sa.PrimaryKeyConstraint('respondent_id_ferc714', 'respondent_id_ferc714_xbrl', name=op.f('pk_core_pudl__assn_ferc714_xbrl_pudl_respondents'))
    )
    with op.batch_alter_table('core_ferc714__respondent_id', schema=None) as batch_op:
        batch_op.add_column(sa.Column('respondent_id_ferc714_csv', sa.Integer(), nullable=True, comment='FERC Form 714 respondent ID from CSV reported data - published from years: 2006-2020. This ID is linked to the newer years of reported XBRL data through the PUDL-assigned respondent_id_ferc714 ID. This ID was originally reported as respondent_id. Note that this ID does not correspond to FERC respondent IDs from other forms.'))
        batch_op.add_column(sa.Column('respondent_id_ferc714_xbrl', sa.Text(), nullable=True, comment='FERC Form 714 respondent ID from XBRL reported data - published from years: 2021-present. This ID is linked to the older years of reported CSV data through the PUDL-assigned respondent_id_ferc714 ID. This ID was originally reported as entity_id. Note that this ID does not correspond to FERC respondent IDs from other forms.'))
        batch_op.create_foreign_key(batch_op.f('fk_core_ferc714__respondent_id_respondent_id_ferc714_core_pudl__assn_ferc714_pudl_respondents'), 'core_pudl__assn_ferc714_pudl_respondents', ['respondent_id_ferc714'], ['respondent_id_ferc714'])

    with op.batch_alter_table('core_ferc714__yearly_planning_area_demand_forecast', schema=None) as batch_op:
        batch_op.add_column(sa.Column('summer_peak_demand_forecast_mw', sa.Float(), nullable=True, comment='The maximum forecasted hourly sumemr load (for the months of June through September).'))
        batch_op.add_column(sa.Column('winter_peak_demand_forecast_mw', sa.Float(), nullable=True, comment='The maximum forecasted hourly winter load (for the months of January through March).'))
        batch_op.add_column(sa.Column('net_demand_forecast_mwh', sa.Float(), nullable=True, comment='Net forecasted electricity demand for the specific period in megawatt-hours (MWh).'))
        batch_op.drop_constraint('fk_core_ferc714__yearly_planning_area_demand_forecast_respondent_id_ferc714_core_ferc714__respondent_id', type_='foreignkey')
        batch_op.create_foreign_key(batch_op.f('fk_core_ferc714__yearly_planning_area_demand_forecast_respondent_id_ferc714_core_pudl__assn_ferc714_pudl_respondents'), 'core_pudl__assn_ferc714_pudl_respondents', ['respondent_id_ferc714'], ['respondent_id_ferc714'])
        batch_op.drop_column('summer_peak_demand_mw')
        batch_op.drop_column('net_demand_mwh')
        batch_op.drop_column('winter_peak_demand_mw')

    with op.batch_alter_table('out_ferc714__respondents_with_fips', schema=None) as batch_op:
        batch_op.drop_constraint('fk_out_ferc714__respondents_with_fips_respondent_id_ferc714_core_ferc714__respondent_id', type_='foreignkey')
        batch_op.create_foreign_key(batch_op.f('fk_out_ferc714__respondents_with_fips_respondent_id_ferc714_core_pudl__assn_ferc714_pudl_respondents'), 'core_pudl__assn_ferc714_pudl_respondents', ['respondent_id_ferc714'], ['respondent_id_ferc714'])

    with op.batch_alter_table('out_ferc714__summarized_demand', schema=None) as batch_op:
        batch_op.drop_constraint('fk_out_ferc714__summarized_demand_respondent_id_ferc714_core_ferc714__respondent_id', type_='foreignkey')
        batch_op.create_foreign_key(batch_op.f('fk_out_ferc714__summarized_demand_respondent_id_ferc714_core_pudl__assn_ferc714_pudl_respondents'), 'core_pudl__assn_ferc714_pudl_respondents', ['respondent_id_ferc714'], ['respondent_id_ferc714'])

    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('out_ferc714__summarized_demand', schema=None) as batch_op:
        batch_op.drop_constraint(batch_op.f('fk_out_ferc714__summarized_demand_respondent_id_ferc714_core_pudl__assn_ferc714_pudl_respondents'), type_='foreignkey')
        batch_op.create_foreign_key('fk_out_ferc714__summarized_demand_respondent_id_ferc714_core_ferc714__respondent_id', 'core_ferc714__respondent_id', ['respondent_id_ferc714'], ['respondent_id_ferc714'])

    with op.batch_alter_table('out_ferc714__respondents_with_fips', schema=None) as batch_op:
        batch_op.drop_constraint(batch_op.f('fk_out_ferc714__respondents_with_fips_respondent_id_ferc714_core_pudl__assn_ferc714_pudl_respondents'), type_='foreignkey')
        batch_op.create_foreign_key('fk_out_ferc714__respondents_with_fips_respondent_id_ferc714_core_ferc714__respondent_id', 'core_ferc714__respondent_id', ['respondent_id_ferc714'], ['respondent_id_ferc714'])

    with op.batch_alter_table('core_ferc714__yearly_planning_area_demand_forecast', schema=None) as batch_op:
        batch_op.add_column(sa.Column('winter_peak_demand_mw', sa.FLOAT(), nullable=True))
        batch_op.add_column(sa.Column('net_demand_mwh', sa.FLOAT(), nullable=True))
        batch_op.add_column(sa.Column('summer_peak_demand_mw', sa.FLOAT(), nullable=True))
        batch_op.drop_constraint(batch_op.f('fk_core_ferc714__yearly_planning_area_demand_forecast_respondent_id_ferc714_core_pudl__assn_ferc714_pudl_respondents'), type_='foreignkey')
        batch_op.create_foreign_key('fk_core_ferc714__yearly_planning_area_demand_forecast_respondent_id_ferc714_core_ferc714__respondent_id', 'core_ferc714__respondent_id', ['respondent_id_ferc714'], ['respondent_id_ferc714'])
        batch_op.drop_column('net_demand_forecast_mwh')
        batch_op.drop_column('winter_peak_demand_forecast_mw')
        batch_op.drop_column('summer_peak_demand_forecast_mw')

    with op.batch_alter_table('core_ferc714__respondent_id', schema=None) as batch_op:
        batch_op.drop_constraint(batch_op.f('fk_core_ferc714__respondent_id_respondent_id_ferc714_core_pudl__assn_ferc714_pudl_respondents'), type_='foreignkey')
        batch_op.drop_column('respondent_id_ferc714_xbrl')
        batch_op.drop_column('respondent_id_ferc714_csv')

    op.drop_table('core_pudl__assn_ferc714_xbrl_pudl_respondents')
    op.drop_table('core_pudl__assn_ferc714_csv_pudl_respondents')
    op.drop_table('core_pudl__assn_ferc714_pudl_respondents')
    # ### end Alembic commands ###