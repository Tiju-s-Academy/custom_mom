from odoo import models, fields, api

class Department(models.Model):
    _inherit = 'hr.department'
    
    color = fields.Integer('Color Index')

class MomMeeting(models.Model):
    _name = 'mom.meeting'
    _description = 'Meeting Minutes'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char('Name', readonly=True)
    meeting_date = fields.Date('Meeting Date', required=True)
    start_time = fields.Float('Start Time')
    end_time = fields.Float('End Time')
    duration = fields.Float('Duration', compute='_compute_duration')
    venue = fields.Selection([
        ('online', 'Online'),
        ('office', 'Office'),
        ('other', 'Other')
    ], string='Venue', default='office')
    location = fields.Char('Location')
    meeting_type_id = fields.Many2one('mom.meeting.type', string='Meeting Type')
    prepared_by_id = fields.Many2one('hr.employee', string='Prepared By', required=True)
    approved_by_id = fields.Many2one('hr.employee', string='Approved By')
    next_meeting_date = fields.Date('Next Meeting Date')
    stage_id = fields.Many2one('mom.stage', string='Stage')
    attendee_ids = fields.Many2many('hr.employee', 'mom_meeting_attendee_rel', 'meeting_id', 'employee_id', string='Attendees')
    absentee_ids = fields.Many2many('hr.employee', 'mom_meeting_absentee_rel', 'meeting_id', 'employee_id', string='Absentees')
    department_ids = fields.Many2many('hr.department', string='Departments')
    discussion_points = fields.Html('Discussion Points')
    current_status = fields.Text('Current Status')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('approved', 'Approved'),
        ('cancelled', 'Cancelled')
    ], string='Status', default='draft', tracking=True)

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

    @api.depends('prepared_by_id', 'state')
    def _compute_readonly_state(self):
        for record in self:
            record.readonly_state = (
                record.prepared_by_id.user_id != self.env.user and
                not self.env.user.has_group('MOM.group_mom_manager')
            )

    readonly_state = fields.Boolean(compute='_compute_readonly_state', store=False)

    # ...existing code...