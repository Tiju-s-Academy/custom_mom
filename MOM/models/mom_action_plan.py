from odoo import models, fields, api, _
from datetime import datetime, timedelta
from odoo.exceptions import UserError, ValidationError

class MomActionPlan(models.Model):
    _name = 'mom.action.plan'
    _description = 'Action Plan'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    # Update all fields to enable tracking
    name = fields.Char('Action Item', required=True, tracking=True)
    mom_id = fields.Many2one('mom.meeting', string='Meeting', required=True, ondelete='cascade', tracking=True)
    meeting_type_id = fields.Many2one(related='mom_id.meeting_type_id', string='Meeting Type', store=True, readonly=True, tracking=True)
    meeting_date = fields.Date(related='mom_id.meeting_date', string='Meeting Date', store=True, readonly=True, tracking=True)
    responsible_id = fields.Many2one('hr.employee', string='Responsible Person', required=True, tracking=True)
    notes = fields.Text('Notes', tracking=True)
    department_id = fields.Many2one(
        'hr.department', 
        string='Department', 
        compute='_compute_department',
        store=True,
        compute_sudo=True,
        tracking=True
    )
    state = fields.Selection([
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('hold', 'Hold'),
        ('completed', 'Completed')
    ], string='Status', default='pending', tracking=True)

    # Fields for action item management
    can_manage_action_items = fields.Boolean(
        string='Can Manage Action Items',
        compute='_compute_can_manage_action_items',
        store=False
    )
    can_edit_state = fields.Boolean(
        string='Can Edit State',
        compute='_compute_can_edit_state',
        store=False
    )

    # New fields for deadline tracking
    deadline = fields.Date('Block Time (Deadline)', required=True, tracking=True)
    completion_date = fields.Date('Completion Date', tracking=True)
    time_status = fields.Selection([
        ('lead_time', 'Lead Time'),
        ('lag_time', 'Lag Time'),
        ('buffer_time', 'Buffer Time'),
        ('cycle_time_1', 'Cycle Time 1'),
        ('cycle_time_2', 'Cycle Time 2'),
        ('cycle_time_3', 'Cycle Time 3'),
        ('cycle_time_4+', 'Cycle Time 4+')
    ], string='Time Status', compute='_compute_time_status', store=True, tracking=True)
    
    cycle_count = fields.Integer('Cycle Extensions', default=0, tracking=True)
    extension_reason = fields.Text('Extension Reason', tracking=True)
    
    # Compute methods
    @api.constrains('deadline')
    def _check_deadline(self):
        for record in self:
            if not record.deadline:
                raise ValidationError(_("Block Time (Deadline) is required for action items."))
    
    @api.depends('deadline', 'completion_date', 'state', 'cycle_count')
    def _compute_time_status(self):
        today = fields.Date.today()
        for record in self:
            if not record.deadline:
                record.time_status = False
                continue
                
            if record.state == 'completed' and record.completion_date:
                if record.completion_date <= record.deadline:
                    record.time_status = 'lead_time'
                else:
                    days_late = (record.completion_date - record.deadline).days
                    record.time_status = record._get_time_status(days_late)
            elif record.state != 'completed':
                if today <= record.deadline:
                    record.time_status = 'lead_time'
                else:
                    days_late = (today - record.deadline).days
                    record.time_status = record._get_time_status(days_late)

    def _get_time_status(self, days_late):
        if days_late <= 2:
            return 'lag_time'
        elif days_late <= 4:
            return 'buffer_time'
        else:
            cycle = (days_late - 4) // 2 + 1
            if cycle >= 4:
                return 'cycle_time_4+'
            return f'cycle_time_{cycle}'

    # Action methods
    def action_extend_deadline(self):
        self.ensure_one()
        if not self.deadline:
            raise UserError(_("Cannot extend deadline: No initial deadline set."))
            
        if not self.env.user.has_group('MOM.group_mom_manager'):
            raise UserError(_("Only MOM managers can extend buffer time."))
            
        if self.time_status == 'lag_time':
            self.write({
                'deadline': fields.Date.today() + timedelta(days=2),
                'extension_reason': _('Buffer time granted by manager'),
            })
        else:
            raise UserError(_("Buffer time can only be granted during lag time period."))

    def action_extend_cycle(self):
        self.ensure_one()
        if not self.deadline:
            raise UserError(_("Cannot extend cycle: No initial deadline set."))
            
        if self.cycle_count >= 4:
            raise UserError(_("Maximum cycle extensions reached."))
            
        self.write({
            'deadline': fields.Date.today() + timedelta(days=2),
            'cycle_count': self.cycle_count + 1
        })

    # Existing code remains unchanged
    @api.depends('responsible_id.department_id')
    def _compute_department(self):
        for record in self:
            record.department_id = record.responsible_id.department_id

    def action_mark_completed(self):
        for record in self:
            record.write({
                'state': 'completed',
                'completion_date': fields.Date.today()
            })
        return True

    @api.depends('mom_id.prepared_by_id')
    def _compute_can_manage_action_items(self):
        for record in self:
            record.can_manage_action_items = (
                record.mom_id.prepared_by_id.user_id == self.env.user or 
                self.env.user.has_group('MOM.group_mom_manager')
            )

    @api.depends('responsible_id', 'mom_id.prepared_by_id')
    def _compute_can_edit_state(self):
        for record in self:
            record.can_edit_state = (
                record.responsible_id.user_id == self.env.user or 
                record.mom_id.prepared_by_id.user_id == self.env.user or
                self.env.user.has_group('MOM.group_mom_manager')
            )

    def write(self, vals):
        # Remove state change restrictions
        return super().write(vals)

    @api.model_create_multi
    def create(self, vals_list):
        if not self.env.user.has_group('MOM.group_mom_manager'):
            for vals in vals_list:
                mom = self.env['mom.meeting'].browse(vals.get('mom_id'))
                if mom.prepared_by_id.user_id != self.env.user:
                    return False
        return super().create(vals_list)

    def unlink(self):
        if not self.env.user.has_group('MOM.group_mom_manager'):
            for record in self:
                if record.mom_id.prepared_by_id.user_id != self.env.user:
                    return False
        return super().unlink()
