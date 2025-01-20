from odoo import models, fields, api

class Department(models.Model):
    _inherit = 'hr.department'
    
    color = fields.Integer('Color Index')

class MomMeeting(models.Model):
    _name = 'mom.meeting'
    # ...existing code...

    @api.model_create_multi
    def create(self, vals_list):
        meetings = super().create(vals_list)
        for meeting in meetings:
            # Add attendees to the attendee group
            attendee_group = self.env.ref('MOM.group_mom_attendee')
            for attendee in meeting.attendee_ids:
                if attendee.user_id:
                    attendee.user_id.write({'groups_id': [(4, attendee_group.id)]})
        return meetings

    def write(self, vals):
        result = super().write(vals)
        if 'attendee_ids' in vals:
            attendee_group = self.env.ref('MOM.group_mom_attendee')
            for meeting in self:
                for attendee in meeting.attendee_ids:
                    if attendee.user_id:
                        attendee.user_id.write({'groups_id': [(4, attendee_group.id)]})
        return result

# ...existing code...