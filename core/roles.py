"""
Role constants and choices for the WaitFree platform.
Hierarchy: Global Admin → Organization → Branch → Operator → Citizen
"""

GLOBAL_ADMIN = 'global_admin'
ORGANIZATION = 'organization'
BRANCH = 'branch'
OPERATOR = 'operator'
CITIZEN = 'citizen'

ROLE_CHOICES = [
    (GLOBAL_ADMIN, 'Global Admin'),
    (ORGANIZATION, 'Organization'),
    (BRANCH, 'Branch'),
    (OPERATOR, 'Operator'),
    (CITIZEN, 'Citizen'),
]

ROLE_HIERARCHY = {
    GLOBAL_ADMIN: 0,
    ORGANIZATION: 1,
    BRANCH: 2,
    OPERATOR: 3,
    CITIZEN: 4,
}

STAFF_ROLES = [GLOBAL_ADMIN, ORGANIZATION, BRANCH, OPERATOR]

PASSWORD_AUTH_ROLES = [GLOBAL_ADMIN, ORGANIZATION, BRANCH, OPERATOR]
OTP_AUTH_ROLES = [CITIZEN]
