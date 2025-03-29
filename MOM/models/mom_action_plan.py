from odoo import models, fields, api

class MomActionPlan(models.Model):
    _name = 'mom.action.plan'
    _description = 'Action Plan'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char('Action Item', required=True, tracking=True)
    mom_id = fields.Many2one('mom.meeting', string='Meeting', required=True, ondelete='cascade')
    meeting_type_id = fields.Many2one(related='mom_id.meeting_type_id', string='Meeting Type', store=True, readonly=True)
    meeting_date = fields.Date(related='mom_id.meeting_date', string='Meeting Date', store=True, readonly=True)
    responsible_id = fields.Many2one('hr.employee', string='Responsible Person', required=True)
    deadline = fields.Date('Deadline')
    notes = fields.Text('Notes')
    department_id = fields.Many2one(
        'hr.department', 
        string='Department', 
        compute='_compute_department',
        store=True,
        compute_sudo=True
    )
    state = fields.Selection([
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed')
    ], string='Status', default='pending', tracking=True)
    can_manage_action_items = fields.Boolean(compute='_compute_can_manage_action_items', store=False)
    can_edit_state = fields.Boolean(compute='_compute_can_edit_state', store=False)

    @api.depends('mom_id.prepared_by_id')
    def _compute_can_manage_action_items(self):
        for record in self:
            record.can_manage_action_items = (
                record.mom_id.prepared_by_id.user_id == self.env.user or 
                self.env.user.has_group('MOM.group_mom_manager')
            )

    @api.depends('responsible_id', 'mom_id.prepared_by_id')
    def _compute_can_edit_state(self):
        for record in self:
            record.can_edit_state = (
                record.responsible_id.user_id == self.env.user or 
                record.mom_id.prepared_by_id.user_id == self.env.user or
                self.env.user.has_group('MOM.group_mom_manager')
            )

    @api.depends('responsible_id.department_id')
    def _compute_department(self):
        for record in self:
            record.department_id = record.responsible_id.department_id

    def write(self, vals):
        # Remove state change restrictions
        return super().write(vals)

    @api.model_create_multi
    def create(self, vals_list):
        if not self.env.user.has_group('MOM.group_mom_manager'):
            for vals in vals_list:
                mom = self.env['mom.meeting'].browse(vals.get('mom_id'))
                if mom.prepared_by_id.user_id != self.env.user:
                    return False
        return super().create(vals_list)

    def unlink(self):
        if not self.env.user.has_group('MOM.group_mom_manager'):
            for record in self:
                if record.mom_id.prepared_by_id.user_id != self.env.user:
                    return False
        return super().unlink()

    def action_mark_completed(self):
        for record in self:
            record.write({'state': 'completed'})
        return True
