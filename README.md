# HostelCare – Hostel Maintenance Request Tracking System

A college-level **DevOps laboratory project** that combines a working Flask web
application with a complete **CI/CD pipeline** (Git → GitHub → Jenkins → Docker →
Pytest → Ansible → Docker Volume).

GitHub: <https://github.com/Vijaykumar-2006/hostel-maintenance-tracker>

---

## 1. Project Description

Students living in a hostel often face problems such as a broken fan, a leaking
tap, a damaged chair or Wi-Fi not working. Usually they must find the warden and
report it verbally, and nobody tracks whether it was fixed.

**HostelCare** solves this:

- A **student** reports a maintenance issue online and instantly receives a
  **Request ID** (e.g. `HM-0001`).
- The **admin / warden** sees every request on a dashboard and updates its status.
- The student uses the Request ID to **track the live status** of the repair.

Status flow:

```
Pending  →  Assigned  →  In Progress  →  Resolved
```

---

## 2. Features

### Student (Resident)
- Clean home page explaining the process
- Report an issue: name, block/room number, issue category, description, priority
- Issue categories: Electrical, Plumbing, Furniture / Carpentry, Wi-Fi / Internet,
  Cleaning / Housekeeping, Other
- Priority: Low / Medium / High
- Receives a Request ID after successful submission
- Tracks the request with a visual progress timeline

### Admin
- Dashboard with summary cards: **Total, Pending, Assigned, In Progress, Resolved**
- Table of all requests: Request ID, student, room, category, description,
  priority, date/time, status
- Update status of any request (stored in SQLite immediately)
- Filter by status and instant search

### Technical
- Server-side input validation with clear success/error messages
- Parameterized SQL queries (safe against SQL injection)
- Database and table are created automatically if they don't exist
- 13 automated Pytest tests using a temporary database
- Responsive UI (works on mobile)

---

## 3. Technology Stack

| Layer      | Technology                         |
|------------|------------------------------------|
| Frontend   | HTML5, CSS3, JavaScript            |
| Backend    | Python 3.11, Flask                 |
| Database   | SQLite (`data/hostel_maintenance.db`) |
| Testing    | Pytest                             |
| DevOps     | Git, GitHub, Jenkins, Docker, Docker Volume, Ansible |

---

## 4. Application Workflow

```
Student
  → Report Issue (category, room, description, priority)
  → Flask (/submit_request validates input)
  → SQLite (row inserted in maintenance_requests)
  → Request ID generated (HM-0001)
  → Student tracks status (/track)

Admin
  → Admin Dashboard (/admin)
  → View Requests
  → Select Request → Choose Status → Update (/update_status)
  → SQLite UPDATE
  → Updated status displayed (dashboard + student's track page)
```

Short form:

```
Student → Report Issue → Flask → SQLite → Admin Dashboard → Status Update
```

---

## 5. DevOps Workflow

```
Developer
   ↓  git push
Git / GitHub
   ↓
Jenkins  (Checkout latest code)
   ↓
Docker Build   →  image: hostel-maintenance-ci
   ↓
Pytest         →  runs inside the image
   ↓
Ansible        →  ansible-docker-lab container runs hostel-deploy.yml
   ↓
Docker Container  →  hostel-maintenance-ansible  (port 5002 → 5000)
   ↓
Flask Application
   ↓
SQLite Database   →  /app/data/hostel_maintenance.db
   ↓
Docker Volume     →  hostel_maintenance_data
```

> **The application flow and the CI/CD flow are separate.**
> Submitting a maintenance request only talks to Flask + SQLite. It never
> triggers Jenkins. Jenkins runs only when the *code* changes (build, test, deploy).

| Tool          | Responsibility                                  |
|---------------|-------------------------------------------------|
| Git / GitHub  | Version control and source code hosting         |
| Jenkins       | Automates Build → Test → Deploy                 |
| Docker        | Packages and runs the Flask application         |
| Pytest        | Verifies the application works before deploying |
| Ansible       | Deploys / configures the Docker container       |
| SQLite        | Stores the maintenance requests                 |
| Docker Volume | Keeps the database safe when containers are recreated |

---

## 6. Project Structure

```
HostelMaintenance/
│
├── app.py                 # Flask application (routes + SQLite logic)
├── requirements.txt       # Flask, pytest
├── Dockerfile             # Builds the hostel-maintenance-ci image
├── Jenkinsfile            # CI/CD pipeline: Checkout → Build → Test → Deploy
├── hostel-deploy.yml      # Ansible playbook (deploys the container)
├── inventory.ini          # Ansible inventory (copied to /inventory.ini)
├── test_app.py            # Pytest test cases
├── .gitignore
├── .dockerignore
├── README.md
│
├── templates/
│   ├── base.html          # Shared layout: navbar + footer
│   ├── index.html         # Home page
│   ├── report.html        # Report Issue form
│   ├── track.html         # Track Request page
│   └── admin.html         # Admin Dashboard
│
├── static/
│   ├── style.css
│   └── script.js
│
└── data/
    └── .gitkeep           # Database is created here (not committed)
```

### Flask routes

| Route             | Method     | Purpose                                 |
|-------------------|------------|-----------------------------------------|
| `/`               | GET        | Home page                               |
| `/report`         | GET        | Report Issue form                       |
| `/submit_request` | POST       | Validate + save request, return Request ID |
| `/track`          | GET / POST | Look up a request by ID                 |
| `/admin`          | GET        | Dashboard with summary cards and table  |
| `/update_status`  | POST       | Change status of a request              |

### Database table: `maintenance_requests`

| Column       | Type    | Notes                                  |
|--------------|---------|----------------------------------------|
| id           | INTEGER | Primary key, auto-increment            |
| student_name | TEXT    |                                        |
| room_number  | TEXT    | Block / room (location)                 |
| category     | TEXT    | Electrical, Plumbing, ...               |
| description  | TEXT    | 10–500 characters                      |
| priority     | TEXT    | Low / Medium / High                    |
| status       | TEXT    | Pending / Assigned / In Progress / Resolved |
| created_at   | TEXT    | Submission date/time                   |
| updated_at   | TEXT    | Last status change                     |

---

## 7. How to Run Locally

```bash
git clone https://github.com/Vijaykumar-2006/hostel-maintenance-tracker.git
cd hostel-maintenance-tracker

python -m venv .venv
# Windows:  .venv\Scripts\activate
# Linux/Mac: source .venv/bin/activate

pip install -r requirements.txt
python app.py
```

Open <http://localhost:5000>. The database is created automatically at
`data/hostel_maintenance.db`.

---

## 8. How to Run Pytest

```bash
python -m pytest test_app.py -v
```

Each test uses a fresh **temporary** database, so tests never depend on an
existing `data/hostel_maintenance.db`. Tests cover:

- Flask app starts
- Home, Report, Track and Admin pages return HTTP 200
- A request can be submitted and is stored in SQLite
- Request ID is shown to the student
- Invalid input is rejected
- Tracking finds existing requests and reports unknown IDs
- Admin dashboard shows database records
- Status updates actually modify SQLite (and invalid statuses are rejected)

---

## 9. Docker

### Build the image

```bash
docker build -t hostel-maintenance-ci .
```

### Run tests inside Docker

```bash
docker run --rm hostel-maintenance-ci python -m pytest test_app.py
```

### Run the container manually (with the Docker Volume)

```bash
docker volume create hostel_maintenance_data

docker run -d \
  --name hostel-maintenance-ansible \
  -p 5002:5000 \
  --restart unless-stopped \
  -v hostel_maintenance_data:/app/data \
  hostel-maintenance-ci
```

Open <http://localhost:5002>.

(In the full pipeline, Ansible creates this container for you.)

---

## 10. Docker Volume – Persistence

| Item            | Value                               |
|-----------------|-------------------------------------|
| Volume name     | `hostel_maintenance_data`           |
| Container path  | `/app/data`                         |
| Database file   | `/app/data/hostel_maintenance.db`   |

A container's own filesystem is deleted when the container is removed. The
SQLite file is therefore stored in a **named Docker Volume**, which lives
outside the container and survives `docker stop`, `docker rm` and redeployments.

**Demo for the viva:**

```bash
# 1. Submit a request at http://localhost:5002 (e.g. gets ID HM-0001)

# 2. Destroy the container completely
docker rm -f hostel-maintenance-ansible

# 3. Recreate it (or re-run the Jenkins pipeline / Ansible playbook)
docker exec ansible-docker-lab ansible-playbook -i /inventory.ini /hostel-deploy.yml

# 4. Track HM-0001 again → the request is still there!

# Inspect the volume
docker volume inspect hostel_maintenance_data
```

---

## 11. Ansible

The playbook `hostel-deploy.yml` uses the **`community.docker.docker_container`**
module to deploy the app:

| Setting         | Value                                   |
|-----------------|-----------------------------------------|
| Container name  | `hostel-maintenance-ansible`            |
| Image           | `hostel-maintenance-ci`                 |
| Ports           | `5002:5000`                             |
| Restart policy  | `unless-stopped`                        |
| Volume          | `hostel_maintenance_data:/app/data`     |
| State           | `{{ container_state \| default('started') }}` |

It also creates the volume with `community.docker.docker_volume` (idempotent).
When a new image is built, the module detects that the image changed and
recreates the container automatically. The volume is untouched, so data is kept.

```bash
# Deploy / update
docker exec ansible-docker-lab ansible-playbook -i /inventory.ini /hostel-deploy.yml

# Stop the app
docker exec ansible-docker-lab ansible-playbook -i /inventory.ini /hostel-deploy.yml -e container_state=stopped

# Remove the container (volume and data are kept)
docker exec ansible-docker-lab ansible-playbook -i /inventory.ini /hostel-deploy.yml -e container_state=absent
```

### One-time setup of the `ansible-docker-lab` container

The Ansible container controls the **host's** Docker engine through the mounted
Docker socket:

```bash
docker run -d --name ansible-docker-lab \
  -v /var/run/docker.sock:/var/run/docker.sock \
  python:3.11-slim sleep infinity

# "ansible" includes the community.docker collection; "docker" is the Python SDK it needs
docker exec ansible-docker-lab pip install ansible docker

docker cp inventory.ini     ansible-docker-lab:/inventory.ini
docker cp hostel-deploy.yml ansible-docker-lab:/hostel-deploy.yml
```

(If your lab already has an `ansible-docker-lab` container with `/inventory.ini`,
skip this. The playbook targets `localhost`, so it works with any inventory.)

---

## 12. Jenkins CI/CD

The `Jenkinsfile` defines a declarative pipeline:

| Stage                   | What happens                                                                 |
|-------------------------|------------------------------------------------------------------------------|
| **Checkout**            | Pulls the latest code from GitHub (`main` branch)                            |
| **Build**               | `docker build -t hostel-maintenance-ci .`                                    |
| **Test**                | `docker run --rm hostel-maintenance-ci python -m pytest test_app.py`         |
| **Deploy with Ansible** | Copies the playbook into the Ansible container, then runs `docker exec ansible-docker-lab ansible-playbook -i /inventory.ini /hostel-deploy.yml` |

If any stage fails, later stages do not run (e.g. failed tests → no deployment).

At the end Jenkins prints:

- ✅ `SUCCESS: HostelCare CI/CD Pipeline Completed Successfully!`
- ❌ `FAILURE: HostelCare CI/CD Pipeline Failed!`

### Setting up the Jenkins job

1. Jenkins must be able to run `docker` commands. For example, run Jenkins in
   Docker with the socket mounted:
   ```bash
   docker run -d --name jenkins -u root -p 8080:8080 \
     -v jenkins_home:/var/jenkins_home \
     -v /var/run/docker.sock:/var/run/docker.sock \
     jenkins/jenkins:lts
   docker exec jenkins bash -c "apt-get update && apt-get install -y docker.io"
   ```
2. In Jenkins: **New Item → Pipeline**.
3. Under *Pipeline*, choose **Pipeline script from SCM → Git**, with repository URL
   `https://github.com/Vijaykumar-2006/hostel-maintenance-tracker.git`, branch `*/main`,
   and script path `Jenkinsfile`.
4. Click **Build Now**.
5. Open <http://localhost:5002> to see the deployed application.

> If Jenkins runs directly on Windows (not in Docker), replace `sh` with `bat`
> in the Jenkinsfile.

---

## 13. Pushing to GitHub

```bash
git add .
git commit -m "Update HostelCare"
git push origin main
```

Then click **Build Now** in Jenkins (or configure a GitHub webhook / Poll SCM to
trigger the pipeline automatically).

---

## 14. Author

**Vijaykumar R** · GitHub: [Vijaykumar-2006](https://github.com/Vijaykumar-2006)
DevOps Laboratory Project
