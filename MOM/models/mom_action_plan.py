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

    # Add recurring fields
    is_recurring = fields.Boolean('Recurring Task', default=False, tracking=True)
    recurrence_days = fields.Integer('Recur Every (Days)', default=1, tracking=True)
    next_deadline = fields.Date('Next Deadline', compute='_compute_next_deadline', store=True)
    
    @api.depends('deadline', 'is_recurring', 'recurrence_days', 'state')
    def _compute_next_deadline(self):
        for record in self:
            if record.is_recurring and record.deadline and record.state != 'completed':
                today = fields.Date.today()
                if today > record.deadline:
                    days_since = (today - record.deadline).days
                    days_to_add = ((days_since // record.recurrence_days) + 1) * record.recurrence_days
                    record.next_deadline = record.deadline + timedelta(days=days_to_add)
                else:
                    record.next_deadline = record.deadline
            else:
                record.next_deadline = record.deadline

    @api.constrains('recurrence_days')
    def _check_recurrence_days(self):
        for record in self:
            if record.is_recurring and record.recurrence_days < 1:
                raise ValidationError(_("Recurrence days must be at least 1"))

    # Override the time status computation for recurring tasks
    @api.depends('deadline', 'completion_date', 'state', 'cycle_count', 'is_recurring', 'next_deadline')
    def _compute_time_status(self):
        today = fields.Date.today()
        for record in self:
            if not record.deadline:
                record.time_status = False
                continue
                
            check_date = record.next_deadline if record.is_recurring else record.deadline
            
            if record.state == 'completed' and record.completion_date:
                if record.completion_date <= check_date:
                    record.time_status = 'lead_time'
                else:
                    days_late = (record.completion_date - check_date).days
                    record.time_status = record._get_time_status(days_late)
            elif record.state != 'completed':
                if today <= check_date:
                    record.time_status = 'lead_time'
                elif not self.env.user.has_group('MOM.group_mom_manager'):
                    # Only auto-move to lag time for non-managers
                    record.time_status = 'lag_time'
                else:
                    days_late = (today - check_date).days
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

    def write(self, vals):
        if 'state' in vals:
            old_state = self.state
            new_state = vals['state']
            
            # Auto-set completion date
            if new_state == 'completed':
                vals['completion_date'] = fields.Date.today()
            elif old_state == 'completed' and new_state != 'completed':
                vals['completion_date'] = False
                
            result = super().write(vals)
            
            # Log the state change
            if result:
                message = _(
                    "Status changed from '%(old)s' to '%(new)s' by %(user)s",
                    old=dict(self._fields['state'].selection).get(old_state),
                    new=dict(self._fields['state'].selection).get(new_state),
                    user=self.env.user.name
                )
                self.message_post(body=message)
            return result
            
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

    @api.depends('mom_id.prepared_by_id', 'responsible_id')
    def _compute_can_manage_action_items(self):
        for record in self:
            record.can_manage_action_items = (
                record.mom_id.prepared_by_id.user_id == self.env.user or
                record.responsible_id.user_id == self.env.user or 
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

    @api.depends('responsible_id.department_id')
    def _compute_department(self):
        for record in self:
            record.department_id = record.responsible_id.department_id
