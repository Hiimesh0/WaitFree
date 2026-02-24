"""
WaitFree Validation Tests — Required tests per specification.

Each test creates the full hierarchy: Org → Branch → Service → Counter → Operator
and then validates a specific enforcement rule.

Tests:
1. Citizen cannot join queue without OTP (unauthenticated = denied)
2. Operator cannot serve out of order (FIFO strictly enforced)
3. Branch cannot see other branches (queryset isolation)
4. Organization cannot see other organizations (queryset isolation)
5. Admin cannot serve queues (role enforcement)
6. Counter close updates ETA (ETA recalculation)
7. No-show works correctly (status update + queue advancement)
"""

from django.test import TestCase, Client
from django.urls import reverse
from django.core.cache import cache

from accounts.models import User
from organizations.models import Organization
from facilities.models import Branch, Service
from counters.models import Counter, OperatorAssignment
from queues.models import QueueTicket
from queues import engine
from core.roles import GLOBAL_ADMIN, ORGANIZATION, BRANCH, OPERATOR, CITIZEN


class BaseTestCase(TestCase):
    """Base test case that sets up the full hierarchy."""

    def setUp(self):
        """Create full hierarchy: Org → Branch → Service → Counter → Operator + Citizen."""
        # Organization
        self.org = Organization.objects.create(
            name='Test Hospital',
            contact_email='test@hospital.com',
        )

        # Branch
        self.branch = Branch.objects.create(
            name='Main Branch',
            organization=self.org,
            address='123 Test St',
        )

        # Service
        self.service = Service.objects.create(
            name='General Consultation',
            branch=self.branch,
            avg_service_time=10,
        )

        # Counter
        self.counter = Counter.objects.create(
            number='1',
            branch=self.branch,
            service=self.service,
            is_open=True,
        )

        # Organization user
        self.org_user = User.objects.create_user(
            username='org_admin',
            password='testpass123',
            role=ORGANIZATION,
            organization=self.org,
        )

        # Branch user
        self.branch_user = User.objects.create_user(
            username='branch_manager',
            password='testpass123',
            role=BRANCH,
            organization=self.org,
            branch=self.branch,
        )

        # Operator
        self.operator = User.objects.create_user(
            username='operator1',
            password='testpass123',
            role=OPERATOR,
            organization=self.org,
            branch=self.branch,
        )
        self.assignment = OperatorAssignment.objects.create(
            user=self.operator,
            counter=self.counter,
        )
        self.counter.current_operator = self.operator
        self.counter.save()

        # Citizen
        self.citizen = User.objects.create_user(
            username='citizen_9876543210',
            password='unusable',
            role=CITIZEN,
            mobile_number='9876543210',
        )
        self.citizen.set_unusable_password()
        self.citizen.save()

        # Global Admin
        self.admin = User.objects.create_user(
            username='superadmin',
            password='testpass123',
            role=GLOBAL_ADMIN,
        )

        self.client = Client()


class TestCitizenCannotJoinWithoutOTP(BaseTestCase):
    """Test 1: Citizen cannot join queue without authentication (OTP verification)."""

    def test_unauthenticated_citizen_cannot_join_queue(self):
        """An unauthenticated user should be redirected from the join queue endpoint."""
        response = self.client.post(
            reverse('queues:join_queue'),
            {'service_id': self.service.id},
        )
        # Should redirect to login (302)
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response.url)

        # No ticket should be created
        self.assertEqual(QueueTicket.objects.count(), 0)

    def test_authenticated_citizen_can_join_queue(self):
        """An authenticated citizen should be able to join a queue."""
        self.client.force_login(self.citizen)
        response = self.client.post(
            reverse('queues:join_queue'),
            {'service_id': self.service.id},
        )
        # Should redirect to ticket page (302)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(QueueTicket.objects.count(), 1)

        ticket = QueueTicket.objects.first()
        self.assertEqual(ticket.citizen, self.citizen)
        self.assertEqual(ticket.service, self.service)
        self.assertEqual(ticket.status, 'waiting')


class TestOperatorCannotServeOutOfOrder(BaseTestCase):
    """Test 2: serve_next always returns the EARLIEST waiting ticket (strict FIFO)."""

    def test_fifo_order_enforced(self):
        """Tickets must be served in FIFO order — no skipping."""
        # Create 3 citizens and join them to the queue in order
        citizens = []
        tickets = []
        for i in range(3):
            c = User.objects.create_user(
                username=f'citizen_{i}',
                role=CITIZEN,
                mobile_number=f'111000000{i}',
            )
            c.set_unusable_password()
            c.save()
            citizens.append(c)
            ticket = engine.join_queue(c, self.service)
            tickets.append(ticket)

        # Serve next should return the FIRST ticket
        served = engine.serve_next(self.counter)
        self.assertEqual(served.id, tickets[0].id)
        self.assertEqual(served.status, 'serving')

        # Complete the first and serve next — should be SECOND
        engine.mark_served(served)
        served2 = engine.serve_next(self.counter)
        self.assertEqual(served2.id, tickets[1].id)

        # Complete second, serve next — should be THIRD
        engine.mark_served(served2)
        served3 = engine.serve_next(self.counter)
        self.assertEqual(served3.id, tickets[2].id)

    def test_no_manual_selection_possible(self):
        """The engine does not accept a ticket_id for serve_next — it always picks FIFO."""
        c1 = User.objects.create_user(username='c_fifo1', role=CITIZEN, mobile_number='2220000001')
        c1.set_unusable_password()
        c1.save()
        c2 = User.objects.create_user(username='c_fifo2', role=CITIZEN, mobile_number='2220000002')
        c2.set_unusable_password()
        c2.save()

        t1 = engine.join_queue(c1, self.service)
        t2 = engine.join_queue(c2, self.service)

        # serve_next only accepts counter — cannot pick t2 first
        served = engine.serve_next(self.counter)
        self.assertEqual(served.id, t1.id)
        self.assertNotEqual(served.id, t2.id)


class TestBranchCannotSeeOtherBranches(BaseTestCase):
    """Test 3: Branch user can only see their own branch data."""

    def test_branch_isolation(self):
        """Branch user's queryset must be filtered to their branch only."""
        # Create another org + branch
        org2 = Organization.objects.create(name='Other Hospital')
        branch2 = Branch.objects.create(name='Other Branch', organization=org2)
        service2 = Service.objects.create(name='X-Ray', branch=branch2, avg_service_time=15)

        branch_user2 = User.objects.create_user(
            username='branch2_mgr',
            password='testpass123',
            role=BRANCH,
            organization=org2,
            branch=branch2,
        )

        # Login as branch 1 user
        self.client.force_login(self.branch_user)
        response = self.client.get(reverse('facilities:manage_services'))
        self.assertEqual(response.status_code, 200)

        # Should see own service but NOT other branch's service
        self.assertContains(response, 'General Consultation')
        self.assertNotContains(response, 'X-Ray')

    def test_branch_dashboard_shows_own_data(self):
        """Branch dashboard only shows data for the user's branch."""
        self.client.force_login(self.branch_user)
        response = self.client.get(reverse('facilities:branch_dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Main Branch')


class TestOrgCannotSeeOtherOrgs(BaseTestCase):
    """Test 4: Organization user can only see their own org's data."""

    def test_organization_isolation(self):
        """Org user's queryset must be filtered to their own organization only."""
        # Create another org with branches
        org2 = Organization.objects.create(name='Rival Hospital')
        branch2 = Branch.objects.create(name='Rival Branch', organization=org2)
        org2_user = User.objects.create_user(
            username='rival_admin',
            password='testpass123',
            role=ORGANIZATION,
            organization=org2,
        )

        # Login as org 1 user
        self.client.force_login(self.org_user)
        response = self.client.get(reverse('organizations:dashboard'))
        self.assertEqual(response.status_code, 200)

        # Should see own branch but NOT rival's branch
        self.assertContains(response, 'Main Branch')
        self.assertNotContains(response, 'Rival Branch')

    def test_org_performance_shows_own_branches(self):
        """Branch performance only shows branches for the org user's organization."""
        org2 = Organization.objects.create(name='Competitor')
        Branch.objects.create(name='Competitor Branch', organization=org2)

        self.client.force_login(self.org_user)
        response = self.client.get(reverse('organizations:branch_performance'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Main Branch')
        self.assertNotContains(response, 'Competitor Branch')


class TestAdminCannotServeQueues(BaseTestCase):
    """Test 5: Admin has visibility but cannot perform operational actions."""

    def test_admin_cannot_access_serve_next(self):
        """Admin should get 403 on serve_next endpoint (operator-only)."""
        self.client.force_login(self.admin)
        response = self.client.post(reverse('queues:serve_next'))
        # Should be 403 (PermissionDenied) or redirect
        self.assertIn(response.status_code, [302, 403])

    def test_admin_cannot_access_operator_dashboard(self):
        """Admin should not access operator dashboard."""
        self.client.force_login(self.admin)
        response = self.client.get(reverse('counters:operator_dashboard'))
        self.assertIn(response.status_code, [302, 403])

    def test_admin_can_access_admin_dashboard(self):
        """Admin should be able to access the admin dashboard."""
        self.client.force_login(self.admin)
        response = self.client.get(reverse('dashboard:admin_dashboard'))
        self.assertEqual(response.status_code, 200)


class TestCounterCloseUpdatesETA(BaseTestCase):
    """Test 6: Closing a counter recalculates ETAs upward."""

    def test_eta_increases_when_counter_closes(self):
        """When a counter closes, ETAs for all waiting tickets should increase."""
        # Create a second counter to have 2 open
        counter2 = Counter.objects.create(
            number='2',
            branch=self.branch,
            service=self.service,
            is_open=True,
        )

        # Create citizens and join queue
        citizens = []
        for i in range(3):
            c = User.objects.create_user(
                username=f'eta_citizen_{i}',
                role=CITIZEN,
                mobile_number=f'333000000{i}',
            )
            c.set_unusable_password()
            c.save()
            engine.join_queue(c, self.service)
            citizens.append(c)

        # Record ETAs with 2 counters open
        tickets_before = list(QueueTicket.objects.filter(
            service=self.service, status='waiting'
        ).values_list('estimated_wait_time', flat=True))

        # Close one counter
        counter2.is_open = False
        counter2.save()
        engine.recalculate_eta(self.service)

        # Get new ETAs (with 1 counter open)
        tickets_after = list(QueueTicket.objects.filter(
            service=self.service, status='waiting'
        ).values_list('estimated_wait_time', flat=True))

        # ETAs should be higher (or equal for position 1) with fewer counters
        for before, after in zip(tickets_before, tickets_after):
            self.assertGreaterEqual(after, before)

    def test_eta_recalculated_on_counter_close_via_view(self):
        """Counter close via the operator view should trigger ETA recalculation."""
        # Join a citizen
        c = User.objects.create_user(
            username='eta_v_citizen',
            role=CITIZEN,
            mobile_number='4440000001',
        )
        c.set_unusable_password()
        c.save()
        engine.join_queue(c, self.service)

        # Operator closes counter via view
        self.client.force_login(self.operator)
        response = self.client.post(
            reverse('counters:counter_control'),
            {'action': 'close'},
        )
        self.assertEqual(response.status_code, 302)

        self.counter.refresh_from_db()
        self.assertFalse(self.counter.is_open)

        # ETA should be -1 (no counters open)
        ticket = QueueTicket.objects.filter(service=self.service, status='waiting').first()
        self.assertIsNotNone(ticket)
        self.assertEqual(ticket.estimated_wait_time, -1)


class TestNoShowWorksCorrectly(BaseTestCase):
    """Test 7: No-show correctly updates status and advances the queue."""

    def test_no_show_marks_status(self):
        """No-show changes ticket status to 'no_show'."""
        c = User.objects.create_user(
            username='noshow_citizen',
            role=CITIZEN,
            mobile_number='5550000001',
        )
        c.set_unusable_password()
        c.save()

        ticket = engine.join_queue(c, self.service)
        served = engine.serve_next(self.counter)
        self.assertEqual(served.status, 'serving')

        engine.mark_no_show(served)
        served.refresh_from_db()
        self.assertEqual(served.status, 'no_show')
        self.assertIsNotNone(served.no_show_at)

    def test_no_show_advances_queue(self):
        """After no-show, the next ticket's position and ETA should update."""
        citizens = []
        for i in range(3):
            c = User.objects.create_user(
                username=f'ns_citizen_{i}',
                role=CITIZEN,
                mobile_number=f'666000000{i}',
            )
            c.set_unusable_password()
            c.save()
            engine.join_queue(c, self.service)
            citizens.append(c)

        # Serve first ticket
        first = engine.serve_next(self.counter)
        self.assertEqual(first.citizen, citizens[0])

        # Mark as no-show
        engine.mark_no_show(first)

        # Check remaining tickets have updated positions
        remaining = QueueTicket.objects.filter(
            service=self.service,
            status='waiting',
        ).order_by('joined_at')

        positions = [t.position for t in remaining]
        # Positions should be 1, 2 (renumbered after no-show)
        self.assertEqual(positions, [1, 2])

    def test_no_show_via_operator_view(self):
        """Operator can mark no-show via the view."""
        c = User.objects.create_user(
            username='ns_view_citizen',
            role=CITIZEN,
            mobile_number='7770000001',
        )
        c.set_unusable_password()
        c.save()

        ticket = engine.join_queue(c, self.service)
        served = engine.serve_next(self.counter)

        self.client.force_login(self.operator)
        response = self.client.post(
            reverse('queues:mark_no_show'),
            {'ticket_id': served.id},
        )
        self.assertEqual(response.status_code, 302)

        served.refresh_from_db()
        self.assertEqual(served.status, 'no_show')
