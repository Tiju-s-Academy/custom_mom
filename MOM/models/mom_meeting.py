from odoo import models, fields, api

class Department(models.Model):
    _inherit = 'hr.department'
    
    color = fields.Integer('Color Index')

class MomMeeting(models.Model):
    _name = 'mom.meeting'
    # ...existing code...

    is_meeting_creator = fields.Boolean(compute='_compute_is_meeting_creator', store=False)

    @api.depends('prepared_by_id')
    def _compute_is_meeting_creator(self):
        for record in self:
            record.is_meeting_creator = (
                record.prepared_by_id.user_id.id == self.env.user.id or
                self.env.user.has_group('MOM.group_mom_manager')
            )

# ...existing code...