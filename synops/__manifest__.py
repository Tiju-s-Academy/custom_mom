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
        'security/synops_security.xml',      # Load security groups first
        'data/sequence_data.xml',            # Then sequences
        'data/activity_data.xml',            # Then activity types
        'security/ir.model.access.csv',      # Then access rights
        'views/synops_mom_views.xml',        # Then views
        'views/synops_action_plan_views.xml',
        'views/menu_views.xml',
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
