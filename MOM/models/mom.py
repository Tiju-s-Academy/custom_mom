from odoo import models, fields, api, _
from odoo.exceptions import UserError

class MemorandumOfMeeting(models.Model):
    _name = 'mom.meeting'
    _description = 'Memorandum of Meeting'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'meeting_date desc'

    name = fields.Char('Reference', required=True, copy=False, readonly=True, 
                      default=lambda self: _('New'))
    meeting_date = fields.Date('Date of Meeting', required=True)
    start_time = fields.Float('Starting Time', required=True)
    end_time = fields.Float('Closing Time', required=True)
    duration = fields.Float(compute='_compute_duration', store=True)
    
    attendee_ids = fields.Many2many('hr.employee', 'mom_attendee_rel', 
                                  'mom_id', 'employee_id', string='Attendees')
    absentee_ids = fields.Many2many('hr.employee', 'mom_absentee_rel', 
                                   'mom_id', 'employee_id', string='Absentees')
    department_ids = fields.Many2many('hr.department', string='Departments')
    
    venue = fields.Selection([
        ('online', 'Online'),
        ('offline', 'Offline')
    ], required=True)
    location = fields.Char('Venue Location')
    
    discussion_points = fields.Html('Discussion Points')
    current_status = fields.Html('Current Status')
    
    action_plan_ids = fields.One2many('mom.action.plan', 'mom_id', 
                                    string='Action Plans')
    
    next_meeting_date = fields.Date('Next Meeting Date')
    prepared_by_id = fields.Many2one('hr.employee', string='Prepared By', 
                                   readonly=True, required=True, default=lambda self: self.env.user.employee_id.id)
    approved_by_id = fields.Many2one('hr.employee', string='Approved By', 
                                   compute='_compute_approved_by', store=True, readonly=True)
    
    state = fields.Selection([
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected')
    ], default='draft', tracking=True)
    
    stage_id = fields.Many2one('mom.stage', string='Stage', 
                              default=lambda self: self.env['mom.stage'].search([], limit=1))

    department_id = fields.Many2one(
        'hr.department', 
        string='Department',
        compute='_compute_department',
        store=True
    )

    meeting_type_id = fields.Many2one(
        'mom.meeting.type',
        string='Meeting Type',
        required=True,
        tracking=True
    )

    @api.depends('start_time', 'end_time')
    def _compute_duration(self):
        for record in self:
            record.duration = record.end_time - record.start_time

    @api.depends('prepared_by_id.department_id')
    def _compute_department(self):
        for record in self:
            record.department_id = record.prepared_by_id.department_id

    @api.depends('prepared_by_id')
    def _compute_approved_by(self):
        for record in self:
            if record.prepared_by_id and record.prepared_by_id.parent_id:
                record.approved_by_id = record.prepared_by_id.parent_id
            else:
                record.approved_by_id = False

    @api.constrains('prepared_by_id')
    def _check_prepared_by(self):
        for record in self:
            if not record.prepared_by_id.user_id == self.env.user:
                raise UserError(_("You can only create meetings for yourself."))

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('mom.meeting') or _('New')
        return super().create(vals_list)

    def action_submit(self):
        for record in self:
            if not record.approved_by_id or not record.approved_by_id.user_id:
                raise UserError(_("Cannot submit for approval: No approver set or approver has no user account."))
            record.state = 'submitted'
            record._create_approval_activity()
        return True

    def _create_approval_activity(self):
        activity_type = self.env.ref('MOM.mail_activity_mom_approval', raise_if_not_found=False)
        if not activity_type:
            raise UserError(_("Activity type 'MOM Approval' not found. Please check the configuration."))

        for record in self:
            if not record.approved_by_id.user_id:
                raise UserError(_("Approver must have a user account to receive activities."))

            vals = {
                'activity_type_id': activity_type.id,
                'note': f'<p>Please review and approve Meeting Minutes: {record.name}</p>',
                'user_id': record.approved_by_id.user_id.id,
                'date_deadline': fields.Date.context_today(self),
                'summary': _('MOM Approval Required'),
                'res_model_id': self.env['ir.model']._get('mom.meeting').id,
                'res_id': record.id,
            }
            try:
                self.env['mail.activity'].create(vals)
            except Exception as e:
                raise UserError(_("Failed to create approval activity: %s") % str(e))

    @api.model
    def get_meetings_domain(self):
        if self.env.user.has_group('MOM.group_mom_manager'):
            return []
        return [('prepared_by_id.user_id', '=', self.env.user.id)]

    @api.model
    def search_read(self, domain=None, fields=None, offset=0, limit=None, order=None):
        if domain is None:
            domain = []
        domain.extend(self.get_meetings_domain())
        return super().search_read(domain=domain, fields=fields, offset=offset, 
                                 limit=limit, order=order)

    @api.onchange('attendee_ids', 'absentee_ids')
    def _onchange_participants(self):
        """Auto-select departments based on attendees and absentees"""
        departments = self.env['hr.department']
        # Get departments from attendees
        if self.attendee_ids:
            departments |= self.attendee_ids.mapped('department_id')
        # Get departments from absentees
        if self.absentee_ids:
            departments |= self.absentee_ids.mapped('department_id')
        
        self.department_ids = departments
