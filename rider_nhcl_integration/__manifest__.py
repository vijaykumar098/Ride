{
    'name': 'NHCL Rider Integration',
    'version': '16.0.0.1',
    'summary': 'NHCL Rider Integration',
    'author': 'New Horizons CyberSoft Ltd',
    'company': 'New Horizons CyberSoft Ltd',
    'maintainer': 'New Horizons CyberSoft Ltd',
    "website": "https://www.nhclindia.com/",
    'description': """Rider MySql to Odoo Integration""",
    'category': 'Connector',
    'depends': ['base', 'account', 'sale', 'sale_subscription','l10n_in'],
    "external_dependencies": {"python": ["sqlalchemy", "mysqlclient"]},
    'data': [
        'security/ir.model.access.csv',
        'views/res_config_setting_view.xml',
        'views/rider_contact_schedule_action_view.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
