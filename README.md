# 🚦 WaitFree — Multi-Tenant Queue Enforcement Platform

WaitFree is a robust **arrival-window and counter-enforcement infrastructure** designed to manage physical queues across multiple organizations and facilities.  
It eliminates the chaos of physical lines by enforcing **who gets served — at the counter — not who stands longest**.

This system is built for **real-world constraints**: walk-ins, staff pressure, lunch breaks, and high-volume public services.

---

## 🧠 Problem Statement

Across hospitals, banks, and government offices, queue systems fail because:

- People arrive early and crowd facilities
- Walk-ins dominate and break order
- Token systems only *display* queues, they don’t enforce them
- Appointment systems don’t handle real-time variance
- Staff face pressure, favoritism claims, and confrontation
- Lunch breaks and counter closures collapse fairness

**Root Cause**  
> Service order is not enforced where it matters most — **at the counter**.

As long as humans decide “who’s next”, queues will be unfair.

---

## 💡 Solution — What WaitFree Fixes

WaitFree solves this by shifting control from **people → system**.

### Core Principle
> **Only the system decides who gets served next. Operators only execute.**

### How WaitFree Solves the Problem

- Citizens join queues **remotely**
- ETA is calculated dynamically using real service throughput
- Citizens arrive **close to their turn**, not hours early
- Operators serve **only the system-assigned citizen**
- Identity is verified at service time (name or mobile)
- No skipping, no favoritism, no silent overrides
- Every action is logged and auditable

This converts queues from **social chaos** into **enforced infrastructure**.

---

## 🚀 Judge's Quick Links
- **Tech Stack**: Django, PostgreSQL, Redis, Selenium (E2E), Dark-Themed CSS.
- **Admin Login**: `admin` / `admin123`
- **Citizen Demo**: `8888000001` (OTP: `123456`)

---

## 📸 UI Showcase

### Landing Page
![Landing Page](screenshots/01_landing.png)

### Employee/Staff Dashboard
![Staff Dashboard](screenshots/10_staff_dashboard.png)

### Citizen Dashboard & Search
![Citizen Dashboard](screenshots/05_citizen_dashboard.png)
![Facility Search](screenshots/06_citizen_search.png)

### Live Ticket Management
![My Tickets](screenshots/07_citizen_my_tickets.png)

---

## 🛠 Key Features

- **Multi-Tenant Hierarchy**: Supports Organizations -> Branches -> Services -> Counters.
- **Advanced Engine**: FIFO-based queue logic with real-time dynamic ETA calculation.
- **Strict RBAC**: 5 distinct roles (Global Admin, Organization, Branch, Operator, and Citizen).
- **Security-First Auth**: Password-based for staff; Passwordless OTP-based for Citizens.
- **Glassmorphism UI**: High-impact modern dark mode built with vanilla CSS.
- **Auditable Workflow**: Comprehensive logging for ticket actions (Join, Serve, No-Show, Complete).

---

## 🏗 Architecture

The system is built on a modular Django architecture with 8 dedicated applications:
- `accounts`: Custom user model with dual auth flows.
- `queues`: Core FIFO engine and ticket lifecycle.
- `facilities`: Branch and service management.
- `counters`: Operator-to-counter assignments.
- `notifications`: OTP handling and turn alerts.

---

## 🚦 How to Run Locally

1. **Clone the repository**:
   ```bash
   git clone <your-repo-url>
   cd "Antigravity v3"
   ```

2. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the Project**:
   ```bash
   python manage.py runserver 8001
   ```

4. **Access the Application**:
   - Open [http://127.0.0.1:8001/](http://127.0.0.1:8001/)

---

## ✅ Verified Workflows
- [x] **OTP Verification**: Citizens can only join after valid mobile authentication.
- [x] **Role Isolation**: Branch managers cannot see other branches' queues.
- [x] **E2E Stability**: Verified with 30+ branches and 200+ concurrent simulated tickets.

Developed by **Himesh Kanthariya** for the **M-Indicator AI Hackathon 2026**.
