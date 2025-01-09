from odoo import models, fields, api

class SynopsActionPlan(models.Model):
    _name = 'synops.action.plan'
    _description = 'Action Plan'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char('Action Item', required=True)
    mom_id = fields.Many2one('synops.mom', string='MOM Reference', required=True)
    assignee_id = fields.Many2one('res.users', string='Assigned To', required=True)
    deadline = fields.Date('Deadline')
    todo_id = fields.Many2one('project.task', string='Related Todo')
    state = fields.Selection([
        ('new', 'New'),
        ('in_progress', 'In Progress'),
        ('done', 'Done'),
        ('cancelled', 'Cancelled')
    ], default='new', tracking=True)
    notes = fields.Text('Notes')

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for record in records:
            record._create_todo_task()
        return records

    def _create_todo_task(self):
        self.ensure_one()
        if not self.todo_id:
            todo = self.env['project.task'].create({
                'name': f"[MOM] {self.name}",
                'user_ids': [(4, self.assignee_id.id)],
                'date_deadline': self.deadline,
                'description': f"Action item from MOM: {self.mom_id.name}\n\n{self.notes or ''}",
                'is_todo': True,
            })
            self.todo_id = todo.id
