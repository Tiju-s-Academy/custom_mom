# Meeting Minutes (MOM) Module

## Overview

The Meeting Minutes (MOM) module is an Odoo application that helps organizations track and manage meeting minutes, action items, and follow-ups. This module allows for efficient documentation of meetings and ensures accountability for action items.

## Features

- **Meeting Management**
  - Create and manage meeting minutes
  - Track meeting dates, times, and durations
  - Document attendees and absentees
  - Record discussion points and current status
  - Organize by departments and meeting types

- **Action Plan Management**
  - Create action items with deadlines
  - Assign responsible persons
  - Track completion status
  - Monitor deadline adherence with time status indicators
  - Allow standalone action items (for managers)
  - Auto-calculate time statuses (lead time, lag time, buffer time, cycle times)

- **Security and Access Control**
  - Three-tiered user roles: Attendee, User, Manager
  - Access control by role and relationship to meeting/action
  - Protection against unauthorized modifications

- **User Experience**
  - Kanban, tree, and form views for easy navigation
  - Color-coded status indicators
  - Clean and intuitive UI

## Technical Structure

### Models

1. `mom.meeting` - Main meeting minutes model
2. `mom.action.plan` - Action items related to meetings
3. `mom.meeting.type` - Types of meetings (configurable)
4. `mom.stage` - Stages for meetings (configurable)

### Views

1. **Meeting Views**
   - Kanban, tree, form views
   - Grouped by meeting type in kanban view

2. **Action Plan Views**
   - Kanban, tree, form views
   - Standalone creation form for managers

3. **Configuration Views**
   - Meeting Types
   - Meeting Stages

### Extension Points

The module is built to be easily extended. Here are the main extension points:

#### 1. Adding New Fields

Add fields to existing models in a custom module:

```python
from odoo import models, fields

class MomMeetingExtended(models.Model):
    _inherit = 'mom.meeting'
    
    custom_field = fields.Char('Custom Field')
```

#### 2. Adding New Features

Create new models that reference the MOM models:

```python
class MomMeetingTemplates(models.Model):
    _name = 'mom.meeting.template'
    _description = 'Meeting Templates'
    
    name = fields.Char('Template Name', required=True)
    meeting_type_id = fields.Many2one('mom.meeting.type', string='Meeting Type')
    template_content = fields.Html('Template Content')
```

#### 3. Extending Views

Extend existing views to add your fields:

```xml
<record id="view_mom_meeting_form_extended" model="ir.ui.view">
    <field name="name">mom.meeting.form.extended</field>
    <field name="model">mom.meeting</field>
    <field name="inherit_id" ref="MOM.view_mom_meeting_form"/>
    <field name="arch" type="xml">
        <xpath expr="//field[@name='location']" position="after">
            <field name="custom_field"/>
        </xpath>
    </field>
</record>
```

## Development Guidelines

### Adding New Fields

1. Consider the purpose of the field
2. Add appropriate tracking if workflow relevant
3. Update views to display the field
4. Add access controls if needed

### Adding New Models

1. Follow the existing pattern for security and access
2. Define relationships to existing models where appropriate
3. Consider inheritance from mail.thread for tracking

### Modifying Workflows

1. Extend or override the relevant methods
2. Maintain backward compatibility
3. Document changes for future developers

## Security Considerations

- Action plans have owner-based permissions
- Managers have full access to all records
- Attendees have read-only access to their meetings and action items
- Users can edit their own records

## Future Development Ideas

1. **Dashboard Integration**
   - Metrics on meeting efficiency
   - Action item completion rates
   - Department participation stats

2. **Automation Features**
   - Auto-reminder emails for pending action items
   - Auto-generation of recurring meetings
   - Integration with calendar module

3. **Reporting**
   - Custom reports for meetings and action items
   - Export options for different formats

## Module Dependencies

- `base`
- `mail`
- `hr`

## License

LGPL-3.0
