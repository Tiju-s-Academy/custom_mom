from odoo import models, fields, api, _
from odoo.exceptions import UserError

class MOMActionPlan(models.Model):
    _name = 'mom.action.plan'
    _description = 'MOM Action Plan'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char('Action Item', required=True)
    mom_id = fields.Many2one('mom.meeting', string='MOM Reference', required=True)
    responsible_id = fields.Many2one('hr.employee', string='Responsible Person', 
                                   required=True)
    deadline = fields.Date('Deadline')
    notes = fields.Text('Notes')
    state = fields.Selection([
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled')
    ], default='pending', tracking=True)
    
    department_id = fields.Many2one(
        'hr.department',
        string='Department',
        related='responsible_id.department_id',
        store=True,
        readonly=True
    )
    
    @api.constrains('mom_id', 'responsible_id')
    def _check_access_rights(self):
        for record in self:
            if not self.env.user.has_group('MOM.group_mom_manager'):
                if record.mom_id.prepared_by_id.user_id != self.env.user:
                    # Only meeting creator can add action items
                    raise UserError(_("You can only create action items for your own meetings."))
    
    def action_mark_completed(self):
        self.write({'state': 'completed'})

    @api.model_create_multi
    def create(self, vals_list):
        # Ensure responsible person is set properly
        for vals in vals_list:
            if not vals.get('responsible_id'):
                vals['responsible_id'] = self.env.user.employee_id.id
        records = super().create(vals_list)
        for record in records:
            record._create_follow_up_activity()
        return records

    def _create_follow_up_activity(self):
        self.activity_schedule(
            'mom.mail_activity_action_plan_follow_up',
            user_id=self.responsible_id.user_id.id,
            date_deadline=self.deadline,
            note=f'Follow up required for action item: {self.name}'
        )
