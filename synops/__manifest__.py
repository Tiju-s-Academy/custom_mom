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
    'depends': ['base', 'mail', 'project_todo'],
    'data': [
        'security/synops_security.xml',  # Security groups must be loaded first
        'security/ir.model.access.csv',
        'data/sequence_data.xml',
        'data/activity_data.xml',
        'views/synops_mom_views.xml',
        'views/synops_action_plan_views.xml',
        'views/menu_views.xml',
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
