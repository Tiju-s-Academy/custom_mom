from odoo import models, fields, api, _
from datetime import datetime, timedelta
from odoo.exceptions import UserError, ValidationError
import logging

_logger = logging.getLogger(__name__)

class MomActionPlan(models.Model):
    _name = 'mom.action.plan'
    _description = 'Action Plan'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'  # Add this line for default ordering

    # Update all fields to enable tracking
    name = fields.Char('Action Item', required=True, tracking=True)
    mom_id = fields.Many2one('mom.meeting', string='Meeting', required=False, ondelete='cascade', tracking=True)
    meeting_type_id = fields.Many2one(
        'mom.meeting.type', 
        string='Meeting Type', 
        store=True, 
        readonly=False,
        tracking=True,
        related='mom_id.meeting_type_id',
        compute='_compute_meeting_data',
        inverse='_inverse_meeting_type')
    meeting_date = fields.Date(
        related='mom_id.meeting_date', 
        string='Meeting Date', 
        store=True, 
        readonly=False,
        compute='_compute_meeting_data',
        tracking=True)
    responsible_id = fields.Many2one('hr.employee', string='Responsible Person', required=True, tracking=True)
    notes = fields.Text('Notes', tracking=True)
    department_id = fields.Many2one(
        'hr.department', 
        compute_sudo=True,', 
        tracking=Truepute_department',
    )   store=True,
    state = fields.Selection([
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('hold', 'Hold'),ion([
        ('completed', 'Completed')
    ], string='Status', default='pending', tracking=True)
        ('hold', 'Hold'),
    # Fields for action item management
    can_manage_action_items = fields.Boolean(acking=True)
        string='Can Manage Action Items',
        compute='_compute_can_manage_action_items',
        store=Falseon_items = fields.Boolean(
    )   string='Can Manage Action Items',
    can_edit_state = fields.Boolean(_action_items',
        string='Can Edit State',
        compute='_compute_can_edit_state',
        store=False= fields.Boolean(
    )   string='Can Edit State',
        compute='_compute_can_edit_state',
    # New fields for deadline tracking
    deadline = fields.Date('Block Time (Deadline)', required=True, tracking=True)
    completion_date = fields.Date('Completion Date', tracking=True)
    time_status = fields.Selection([ng
        ('lead_time', 'Lead Time'),ime (Deadline)', required=True, tracking=True)
        ('lag_time', 'Lag Time'),('Completion Date', tracking=True)
        ('buffer_time', 'Buffer Time'),
        ('cycle_time_1', 'Cycle Time 1'),
        ('cycle_time_2', 'Cycle Time 2'),
        ('cycle_time_3', 'Cycle Time 3'),
        ('cycle_time_4+', 'Cycle Time 4+')
    ], string='Time Status', compute='_compute_time_status', store=True, tracking=True)
        ('cycle_time_3', 'Cycle Time 3'),
    cycle_count = fields.Integer('Cycle Extensions', default=0, tracking=True)
    extension_reason = fields.Text('Extension Reason', tracking=True)ue, tracking=True)
    
    # Add recurring fieldsnteger('Cycle Extensions', default=0, tracking=True)
    is_recurring = fields.Boolean('Recurring Task', default=False, tracking=True)
    recurrence_days = fields.Integer('Recur Every (Days)', default=1, tracking=True)
    next_deadline = fields.Date('Next Deadline', compute='_compute_next_deadline', store=True)
    is_recurring = fields.Boolean('Recurring Task', default=False, tracking=True)
    # New countdown fieldlds.Integer('Recur Every (Days)', default=1, tracking=True)
    days_to_deadline = fields.Integer(Deadline', compute='_compute_next_deadline', store=True)
        string='Days Left', 
        compute='_compute_days_to_deadline',
        store=True,e = fields.Integer(
    )   string='Days Left', 
        compute='_compute_days_to_deadline',
    countdown_status = fields.Selection([
        ('green', 'Green'),
        ('yellow', 'Yellow'),
        ('orange', 'Orange'),.Selection([
        ('red', 'Red'),n'),
    ], string='Countdown Status', compute='_compute_days_to_deadline', store=True)
        ('orange', 'Orange'),
    @api.depends('deadline', 'is_recurring', 'recurrence_days', 'state')
    def _compute_next_deadline(self):pute='_compute_days_to_deadline', store=True)
        for record in self:
            if record.is_recurring and record.deadline and record.state != 'completed':
                today = fields.Date.today()
                if today > record.deadline:
                    days_since = (today - record.deadline).daysrd.state != 'completed':
                    days_to_add = ((days_since // record.recurrence_days) + 1) * record.recurrence_days
                    record.next_deadline = record.deadline + timedelta(days=days_to_add)
                else:ays_since = (today - record.deadline).days
                    record.next_deadline = record.deadlineecurrence_days) + 1) * record.recurrence_days
            else:   record.next_deadline = record.deadline + timedelta(days=days_to_add)
                record.next_deadline = record.deadline
                    record.next_deadline = record.deadline
    @api.constrains('recurrence_days')
    def _check_recurrence_days(self):= record.deadline
        for record in self:
            if record.is_recurring and record.recurrence_days < 1:
                raise ValidationError(_("Recurrence days must be at least 1"))
        for record in self:
    # Override the time status computation for recurring tasks< 1:
    @api.depends('deadline', 'completion_date', 'state', 'cycle_count', 'is_recurring', 'next_deadline')
    def _compute_time_status(self):
        today = fields.Date.today()utation for recurring tasks
        for record in self:, 'completion_date', 'state', 'cycle_count', 'is_recurring', 'next_deadline')
            if not record.deadline:
                record.time_status = False
                continuelf:
                ot record.deadline:
            check_date = record.next_deadline if record.is_recurring else record.deadline
                continue
            if record.state == 'completed' and record.completion_date:
                if record.completion_date <= check_date:is_recurring else record.deadline
                    record.time_status = 'lead_time'
                else:.state == 'completed' and record.completion_date:
                    days_late = (record.completion_date - check_date).days
                    record.time_status = record._get_time_status(days_late)
            elif record.state != 'completed':
                if today <= check_date:.completion_date - check_date).days
                    record.time_status = 'lead_time'_time_status(days_late)
                elif not self.env.user.has_group('MOM.group_mom_manager'):
                    # Only auto-move to lag time for non-managers
                    record.time_status = 'lag_time''
                else:not self.env.user.has_group('MOM.group_mom_manager'):
                    days_late = (today - check_date).daysmanagers
                    record.time_status = record._get_time_status(days_late)
                else:
    def _get_time_status(self, days_late):heck_date).days
        if days_late <= 2:.time_status = record._get_time_status(days_late)
            return 'lag_time'
        elif days_late <= 4:f, days_late):
            return 'buffer_time'
        else:eturn 'lag_time'
            cycle = (days_late - 4) // 2 + 1
            if cycle >= 4:_time'
                return 'cycle_time_4+'
            return f'cycle_time_{cycle}' + 1
            if cycle >= 4:
    def write(self, vals):cle_time_4+'
        if 'state' in vals:time_{cycle}'
            old_state = self.state
            new_state = vals['state']
            state' in vals:
            # Auto-set completion date
            if new_state == 'completed':
                vals['completion_date'] = fields.Date.today()
            elif old_state == 'completed' and new_state != 'completed':
                vals['completion_date'] = False
                vals['completion_date'] = fields.Date.today()
            result = super().write(vals)' and new_state != 'completed':
                vals['completion_date'] = False
            # Log the state change
            if result:uper().write(vals)
                message = _(
                    "Status changed from '%(old)s' to '%(new)s' by %(user)s",
                    old=dict(self._fields['state'].selection).get(old_state),
                    new=dict(self._fields['state'].selection).get(new_state),
                    user=self.env.user.name(old)s' to '%(new)s' by %(user)s",
                )   old=dict(self._fields['state'].selection).get(old_state),
                self.message_post(body=message)e'].selection).get(new_state),
            return resultself.env.user.name
                )
        return super().write(vals)body=message)
            return result
    @api.model_create_multi
    def create(self, vals_list):s)
        for vals in vals_list:
            # Only require mom_id for non-managers
            if not self.env.user.has_group('MOM.group_mom_manager') and not vals.get('mom_id'):
                return Falset:
            elif vals.get('mom_id') and not self.env.user.has_group('MOM.group_mom_manager'):
                mom = self.env['mom.meeting'].browse(vals.get('mom_id'))not vals.get('mom_id'):
                if mom.prepared_by_id.user_id != self.env.user:
                    return Falsed') and not self.env.user.has_group('MOM.group_mom_manager'):
        return super().create(vals_list)ing'].browse(vals.get('mom_id'))
                if mom.prepared_by_id.user_id != self.env.user:
    def unlink(self):eturn False
        if not self.env.user.has_group('MOM.group_mom_manager'):
            for record in self:
                if record.mom_id.prepared_by_id.user_id != self.env.user:
                    return False_group('MOM.group_mom_manager'):
        return super().unlink()
                if record.mom_id.prepared_by_id.user_id != self.env.user:
    @api.depends('mom_id.prepared_by_id', 'responsible_id')
    def _compute_can_manage_action_items(self):
        for record in self:
            record.can_manage_action_items = (ponsible_id')
                record.mom_id.prepared_by_id.user_id == self.env.user or
                record.responsible_id.user_id == self.env.user or 
                self.env.user.has_group('MOM.group_mom_manager')
            )   record.mom_id.prepared_by_id.user_id == self.env.user or
                record.responsible_id.user_id == self.env.user or 
    @api.depends('responsible_id', 'mom_id.prepared_by_id') er')
    def _compute_can_edit_state(self):
        for record in self:
            record.can_edit_state = (om_id.prepared_by_id') 
                record.responsible_id.user_id == self.env.user or
                record.mom_id.prepared_by_id.user_id == self.env.user or
                self.env.user.has_group('MOM.group_mom_manager')
            )   record.responsible_id.user_id == self.env.user or
                record.mom_id.prepared_by_id.user_id == self.env.user or
    @api.depends('responsible_id.department_id')up_mom_manager')
    def _compute_department(self):
        for record in self:
            record.department_id = record.responsible_id.department_id
    def _compute_department(self):
    @api.depends('mom_id'):
    def _compute_meeting_data(self):ecord.responsible_id.department_id
        for record in self:
            if record.mom_id:
                record.meeting_type_id = record.mom_id.meeting_type_id
                record.meeting_date = record.mom_id.meeting_date
            elif not record.meeting_type_id:
                # Set default meeting typeecord.mom_id.meeting_type_id
                meeting_type = self.env['mom.meeting.type'].search([], limit=1)
                if meeting_type:ing_type_id:
                    record.meeting_type_id = meeting_type.id
                meeting_type = self.env['mom.meeting.type'].search([], limit=1)
    def _inverse_meeting_type(self):
        # This method is required for the inverse field to work properly
        pass
    def _inverse_meeting_type(self):
    @api.depends('deadline')uired for the inverse field to work properly
    def _compute_days_to_deadline(self):
        today = fields.Date.today()
        for record in self:)
            if not record.deadline:elf):
                record.days_to_deadline = 0
                record.countdown_status = 'green'
                continued.deadline:
                record.days_to_deadline = 0
            days = (record.deadline - today).days
            record.days_to_deadline = days
            
            # Set countdown status based on days left
            if days <= 0:o_deadline = days
                record.countdown_status = 'red'
            elif days <= 3: status based on days left
                record.countdown_status = 'orange'
            elif days <= 7:tdown_status = 'red'
                record.countdown_status = 'yellow'
            else:ecord.countdown_status = 'orange'
                record.countdown_status = 'green'
                record.countdown_status = 'yellow'
            else:
                record.countdown_status = 'green'
                
    # Method for cron job to update countdown days
    @api.model
    def update_countdown_days(self):
        """Update countdown days for all active action plans"""
        # Only update non-completed action plans
        action_plans = self.search([('state', '!=', 'completed')])
        for plan in action_plans:
            # Trigger compute method by writing to a dummy field
            # This avoids having to duplicate the logic
            plan._compute_days_to_deadline()
            
        _logger.info(f"Updated countdown days for {len(action_plans)} action plans")
        return True
