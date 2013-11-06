APP_V1 = '1.0'
APP_V2 = '2.0'

CAREPLAN_GOAL = 'goal'
CAREPLAN_TASK = 'task'

CAREPLAN_DEFAULT_CASE_PROPERTIES = {
    CAREPLAN_GOAL: {
        'create': {
            'description': '/data/description',
            'date_followup': '/data/date_followup',
        },
        'update': {
            'description': '/data/description',
            'date_followup': '/data/date_followup',
        },
    },
    CAREPLAN_TASK: {
        'create': {
            'description': '/data/description',
            'date_followup': '/data/date_followup',
        },
        'update': {
            'description': '/data/description',
            'date_followup': '/data/date_followup',
            'latest_report': '/data/progress_update'
        }
    },
}

CAREPLAN_NAME_PATH = '/data/name'