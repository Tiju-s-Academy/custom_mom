from odoo import models, fields, api

class MOMActionPlan(models.Model):
    _name = 'mom.action.plan'
    _description = 'MOM Action Plan'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char('Action Item', required=True)
    mom_id = fields.Many2one('mom.meeting', string='MOM Reference', required=True)
    responsible_id = fields.Many2one('hr.employee', string='Responsible Person', 
                                   required=True)
    deadline = fields.Date('Deadline')
    state = fields.Selection([
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled')
    ], default='pending', tracking=True)
    
    notes = fields.Text('Notes')
    
    def action_mark_completed(self):
        self.write({'state': 'completed'})

    @api.model_create_multi
    def create(self, vals_list):
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
