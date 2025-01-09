from odoo import models, fields, api, _
from odoo.exceptions import UserError

class SynopsMOM(models.Model):
    _name = 'synops.mom'
    _description = 'Meeting Minutes'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'meeting_date desc, id desc'

    name = fields.Char('Reference', required=True, copy=False, readonly=True, default=lambda self: _('New'))
    meeting_date = fields.Date('Date of Meeting', required=True)
    start_time = fields.Float('Starting Time', required=True)
    end_time = fields.Float('Closing Time', required=True)
    duration = fields.Float(compute='_compute_duration', store=True)
    attendee_ids = fields.Many2many('res.users', string='Attendees')
    absentee_ids = fields.Many2many('res.users', 'mom_absentee_rel', string='Absentees')
    department_ids = fields.Many2many('hr.department', string='Departments')
    venue = fields.Selection([('online', 'Online'), ('offline', 'Offline')], required=True)
    location = fields.Char('Venue Details')
    discussion_points = fields.Html('Discussion Points')
    current_status = fields.Html('Current Status')
    action_plan_ids = fields.One2many('synops.action.plan', 'mom_id', string='Action Plans')
    next_meeting_date = fields.Date('Next Meeting Date')
    prepared_by_id = fields.Many2one('res.users', string='Prepared By', default=lambda self: self.env.user)
    approved_by_id = fields.Many2one('res.users', string='Approved By', tracking=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('approved', 'Approved'),
        ('cancelled', 'Cancelled')
    ], default='draft', tracking=True)

    @api.depends('start_time', 'end_time')
    def _compute_duration(self):
        for record in self:
            record.duration = record.end_time - record.start_time

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('synops.mom') or _('New')
        return super().create(vals_list)

    def action_submit(self):
        self.state = 'submitted'
        self._create_approval_activity()

    def action_approve(self):
        if not self.env.user.has_group('synops.group_synops_manager'):
            raise UserError(_('Only managers can approve MOMs'))
        self.write({
            'state': 'approved',
            'approved_by_id': self.env.user.id
        })

    def action_cancel(self):
        self.state = 'cancelled'

    def _create_approval_activity(self):
        manager = self.env.user.employee_id.parent_id.user_id
        if manager:
            self.activity_schedule(
                'synops.mail_activity_mom_approval',
                user_id=manager.id,
                note=_('Please review and approve the MOM: %s') % self.name
            )
