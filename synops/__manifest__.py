{
    'name': 'Synops - Meeting Minutes Manager',
    'version': '17.0.1.0.0',
    'category': 'Productivity/Meetings',
    'summary': 'Manage Meeting Minutes and Action Plans',
    'description': """
        Create and manage Meeting Minutes (MOM) with:
        * Action Plans tracking
        * Manager approvals
        * Follow-ups and Activities
        * Todo integration
    """,
    'depends': ['base', 'mail', 'project_todo', 'hr'],  # Add hr dependency
    'data': [
        'security/synops_security.xml',      # Security groups first
        'views/synops_mom_views.xml',        # Load views before access rights to create models
        'views/synops_action_plan_views.xml',
        'security/ir.model.access.csv',      # Then load access rights
        'data/sequence_data.xml',            # Sequences third
        'data/activity_data.xml',            # Activity types fourth
        'views/menu_views.xml',              # Views last
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
