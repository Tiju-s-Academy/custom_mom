from odoo import models, fields, api

class Department(models.Model):
    _inherit = 'hr.department'
    
    color = fields.Integer('Color Index')

class MomMeeting(models.Model):
    _name = 'mom.meeting'
    _description = 'Meeting Minutes'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    
    def can_edit(self):
        self.ensure_one()
        return (
            self.prepared_by_id.user_id == self.env.user or 
            self.env.user.has_group('MOM.group_mom_manager')
        )

    # ...existing code...