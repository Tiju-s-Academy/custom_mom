from odoo import models, fields, api

class Department(models.Model):
    _inherit = 'hr.department'
    
    color = fields.Integer('Color Index')

class MomMeeting(models.Model):
    _name = 'mom.meeting'
    _description = 'Meeting Minutes'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char('Name', readonly=True)
    meeting_date = fields.Date('Meeting Date', required=True, tracking=True)
    start_time = fields.Float('Start Time', tracking=True)
    end_time = fields.Float('End Time', tracking=True)
    duration = fields.Float('Duration', compute='_compute_duration', store=True)
    venue = fields.Selection([
        ('online', 'Online'),
        ('office', 'Office'),
        ('other', 'Other')
    ], string='Venue', default='office', tracking=True)
    location = fields.Char('Location', tracking=True)
    meeting_type_id = fields.Many2one('mom.meeting.type', string='Meeting Type', tracking=True)
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
    is_creator = fields.Boolean(compute='_compute_is_creator', store=False)
    manager_group = fields.Many2many('res.users', compute='_compute_manager_group')

    def _check_can_edit(self):
        """Check if current user can edit the record"""
        self.ensure_one()
        return (
            self.prepared_by_id.user_id == self.env.user or 
            self.env.user.has_group('MOM.group_mom_manager')
        )

    @api.depends('start_time', 'end_time')
    def _compute_duration(self):
        for record in self:
            if record.start_time and record.end_time:
                record.duration = record.end_time - record.start_time
            else:
                record.duration = 0.0

    @api.depends('prepared_by_id', 'create_uid')
    def _compute_is_creator(self):
        for record in self:
            record.is_creator = (
                (record.prepared_by_id and record.prepared_by_id.user_id == self.env.user) or
                (not record.id) or  # New record
                record.create_uid == self.env.user or
                self.env.user.has_group('MOM.group_mom_manager')
            )

    @api.depends_context('uid')
    def _compute_manager_group(self):
        manager_group = self.env.ref('MOM.group_mom_manager').users.ids
        for record in self:
            record.manager_group = manager_group

    @api.model
    def create(self, vals):
        if not vals.get('prepared_by_id'):
            employee = self.env['hr.employee'].search([('user_id', '=', self.env.user.id)], limit=1)
            if employee:
                vals['prepared_by_id'] = employee.id
        return super().create(vals)

    def write(self, vals):
        # Always allow managers to edit
        if self.env.user.has_group('MOM.group_mom_manager'):
            return super().write(vals)
            
        # For normal users, only allow if they're the creator and in draft state
        for record in self:
            if record.prepared_by_id.user_id == self.env.user and record.state == 'draft':
                return super(MomMeeting, self).write(vals)
            
        return super(MomMeeting, self).write(vals)