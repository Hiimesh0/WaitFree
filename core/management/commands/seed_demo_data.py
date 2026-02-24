import random
from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth import get_user_model
from organizations.models import Organization
from facilities.models import Branch, Service
from counters.models import Counter, OperatorAssignment
from queues.models import QueueTicket
from queues.engine import join_queue, serve_next, mark_served
from core.roles import ORGANIZATION, BRANCH, OPERATOR, CITIZEN

User = get_user_model()

class Command(BaseCommand):
    help = 'Seeds the database with scaled demo data for WaitFree platform'

    def handle(self, *args, **kwargs):
        self.stdout.write('Cleaning up old demo data...')
        
        # Delete demo users
        User.objects.filter(username__startswith='org_').delete()
        User.objects.filter(username__startswith='op_').delete()
        User.objects.filter(username__startswith='citizen_').delete()
        User.objects.filter(username__contains='_mgr').delete()
        User.objects.exclude(username='admin').delete() # Clean everything except superuser
        
        # Delete demo data
        Organization.objects.all().delete()

        self.stdout.write('Seeding SCALED demo data...')

        # 1. Sector Definitions
        sectors = [
            {
                'type': 'Health',
                'orgs': ['City General Hospital', 'LifeCare Clinics', 'Wellness Health'],
                'services': [
                    {'name': 'General Medicine', 'avg': 10, 'desc': 'Standard checkups'},
                    {'name': 'Pediatrics', 'avg': 15, 'desc': 'Child care'},
                    {'name': 'Dental', 'avg': 20, 'desc': 'Orthodontics'}
                ]
            },
            {
                'type': 'Banking',
                'orgs': ['Global Trust Bank', 'Metro Savings', 'First Choice Finance'],
                'services': [
                    {'name': 'Cash Deposits', 'avg': 5, 'desc': 'Counter cash transactions'},
                    {'name': 'Loans & Credit', 'avg': 30, 'desc': 'Consultation for loans'},
                    {'name': 'Account Services', 'avg': 15, 'desc': 'New accounts and KYC'}
                ]
            },
            {
                'type': 'Government',
                'orgs': ['Passport Seva Kendra', 'Regional Transport Office (RTO)', 'Municipal Corporation'],
                'services': [
                    {'name': 'New Applications', 'avg': 20, 'desc': 'First time registration'},
                    {'name': 'Renewals', 'avg': 12, 'desc': 'Document renewal'},
                    {'name': 'Verification', 'avg': 15, 'desc': 'Physical verification'}
                ]
            }
        ]

        # 2. Locations
        cities = ['Bengaluru', 'Hyderabad', 'Mumbai', 'Delhi', 'Chennai', 'Pune']
        areas = ['Indiranagar', 'Koramangala', 'HSR Layout', 'Whitefield', 'Jayanagar', 'MG Road']

        # 3. Create Organizations, Branches, Services, Counters, Operators
        all_services = []
        for sector in sectors:
            for org_name in sector['orgs']:
                slug = org_name.lower().replace(' ', '-').replace('(', '').replace(')', '')
                org, _ = Organization.objects.get_or_create(
                    name=org_name,
                    slug=slug,
                    defaults={
                        'contact_email': f"contact@{slug}.com",
                        'phone': f"+91 {random.randint(70000, 99999)} {random.randint(10000, 99999)}",
                        'is_active': True
                    }
                )

                # Org Admin
                org_admin, _ = User.objects.get_or_create(
                    username=f"org_admin_{slug.replace('-', '_')}",
                    defaults={
                        'email': f"admin@{slug}.com",
                        'role': ORGANIZATION,
                        'organization': org
                    }
                )
                org_admin.set_password('admin123')
                org_admin.save()

                # 3-5 Branches per Organization
                num_branches = random.randint(3, 5)
                for b_idx in range(num_branches):
                    city = random.choice(cities)
                    area = random.choice(areas)
                    branch_name = f"{org_name} - {city} {area} #{b_idx + 1}"
                    branch, _ = Branch.objects.get_or_create(
                        name=branch_name,
                        organization=org,
                        defaults={
                            'address': f"{random.randint(1, 999)} {area}, {city}",
                            'city': city,
                            'is_active': True
                        }
                    )

                    # Branch Manager
                    mgr_username = f"mgr_{slug.replace('-', '_')}_{b_idx}"
                    b_mgr, _ = User.objects.get_or_create(
                        username=mgr_username,
                        defaults={
                            'role': BRANCH,
                            'organization': org,
                            'branch': branch
                        }
                    )
                    b_mgr.set_password('admin123')
                    b_mgr.save()

                    # Services for this branch
                    counter_global_idx = 1
                    for s_data in sector['services']:
                        service, _ = Service.objects.get_or_create(
                            name=s_data['name'],
                            branch=branch,
                            defaults={
                                'avg_service_time': s_data['avg'],
                                'description': s_data['desc'],
                                'is_active': True
                            }
                        )
                        all_services.append(service)

                        # 2 Counters per service
                        for _ in range(2):
                            counter, _ = Counter.objects.get_or_create(
                                number=f"{counter_global_idx}",
                                branch=branch,
                                defaults={
                                    'service': service,
                                    'is_open': True
                                }
                            )

                            # Operator
                            op_username = f"op_{slug.replace('-', '_')}_{b_idx}_{service.id}_{counter_global_idx}"
                            operator, _ = User.objects.get_or_create(
                                username=op_username,
                                defaults={
                                    'role': OPERATOR,
                                    'organization': org,
                                    'branch': branch
                                }
                            )
                            operator.set_password('admin123')
                            operator.save()

                            # Assign
                            OperatorAssignment.objects.get_or_create(user=operator, counter=counter)
                            counter.current_operator = operator
                            counter.save()
                            counter_global_idx += 1

                self.stdout.write(f'  Created {org_name} with {num_branches} branches.')

        # 4. Create Citizens (150+)
        citizen_count = 150
        citizens = []
        
        # Specific citizen for E2E tests
        test_citizen, _ = User.objects.get_or_create(
            username="citizen_9999922222",
            defaults={
                'role': CITIZEN,
                'mobile_number': "9999922222"
            }
        )
        citizens.append(test_citizen)

        for i in range(citizen_count - 1):
            mobile = f"9{random.randint(100000000, 999999999)}"
            citizen, _ = User.objects.get_or_create(
                username=f"citizen_{mobile}",
                defaults={
                    'role': CITIZEN,
                    'mobile_number': mobile
                }
            )
            citizens.append(citizen)

        self.stdout.write(f'  Created {len(citizens)} sample Citizens.')

        # 5. Populate hundreds of tickets
        for citizen in citizens:
            # Each citizen joins 1-2 random UNIQUE services
            num_queues = min(len(all_services), random.randint(1, 2))
            chosen_services = random.sample(all_services, num_queues)
            for service in chosen_services:
                try:
                    ticket = join_queue(citizen, service)
                    
                    # Randomly mark some as served or serving
                    rand = random.random()
                    if rand < 0.6: # 60% are already served
                        ticket.status = 'serving'
                        ticket.called_at = timezone.now() - timedelta(minutes=random.randint(5, 60))
                        ticket.save()
                        mark_served(ticket)
                    elif rand < 0.8: # 20% are currently serving
                        ticket.status = 'serving'
                        ticket.called_at = timezone.now() - timedelta(minutes=random.randint(1, 5))
                        ticket.save()
                    # 20% stay as 'waiting'
                except ValueError:
                    # Skip if validation fails (e.g. no counters open, though script opens them)
                    continue

        self.stdout.write(self.style.SUCCESS(f'Successfully seeded SCALED demo data:'))
        self.stdout.write(f'  - Organizations: {Organization.objects.count()}')
        self.stdout.write(f'  - Branches: {Branch.objects.count()}')
        self.stdout.write(f'  - Services: {Service.objects.count()}')
        self.stdout.write(f'  - Citizens: {len(citizens)}')
        self.stdout.write(f'  - Total Tickets: {QueueTicket.objects.count()}')
