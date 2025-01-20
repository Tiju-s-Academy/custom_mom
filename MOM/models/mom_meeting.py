from odoo import models, fields, api

class Department(models.Model):
    _inherit = 'hr.department'
    
    color = fields.Integer('Color Index')

class MomMeeting(models.Model):
    _name = 'mom.meeting'
    _description = 'Meeting Minutes'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    
    can_edit = fields.Boolean(
        string='Can Edit',
        compute='_compute_can_edit',
        store=False,
        help='Technical field to control edit rights'
    )

    @api.depends('prepared_by_id.user_id')
    def _compute_can_edit(self):
        for record in self:
            record.can_edit = (
                record.prepared_by_id.user_id == self.env.user or 
                self.env.user.has_group('MOM.group_mom_manager')
            )

    # ...existing code...