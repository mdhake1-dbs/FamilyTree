# FamilyTree Vault

A privacy-first web application for recording, visualizing, and preserving family history. Built with Flask and SQLite, it includes hierarchical graphs, timelines, photo management, and comprehensive data export capabilities.

## Overview

FamilyTree Vault helps families preserve their history securely on their own infrastructure. It provides tools for managing family relationships, stories, photos, and historical records without relying on third-party services.

The application is built with modern web technologies and follows infrastructure-as-code principles for deployment. All family data stays under your control.

## Features

### Core functionality
- Create and maintain complex family relationships
- Detailed person profiles with photos, stories, and vital statistics
- Track parent-child, sibling, spouse, and extended family relationships
- Timeline visualization across generations
- Upload and organize family photos with context
- Record and preserve family stories and memories

### Data management
- GEDCOM import/export for standard genealogy format compatibility
- JSON export for custom integrations
- Revision history to track changes
- Automated duplicate detection
- Data validation for consistency

### Privacy and security
- Self-hosted deployment with complete data control
- Access control for viewing and editing permissions
- Encrypted storage and transmission
- Audit logging for all modifications

## Technology Stack

**Frontend**
- HTML5, CSS3, JavaScript (ES6+)

**Backend**
- Python 3.12
- Flask 2.0+
- SQLite

**Infrastructure**
- Terraform for AWS EC2 provisioning
- Ansible for configuration management
- Docker for containerization
- GitHub Actions for CI/CD

## Repository Structure

```
FamilyTree/
├── ansible/
│   ├── hosts.ini           # Inventory file with target hosts
│   └── playbook.yml        # Main playbook for server configuration
│
├── app/
│   ├── backend/
│   │   ├── auth_utils.py   # JWT and password hashing
│   │   ├── config.py       # Application configuration
│   │   ├── database.py     # Database utilities
│   │   ├── main.py         # Flask application entry point
│   │   └── routes/
│   │       ├── auth_routes.py
│   │       ├── events_routes.py
│   │       ├── misc_routes.py
│   │       ├── people_routes.py
│   │       └── relationships_routes.py
│   │
│   ├── db/
│   │   └── 01_schema_sqlite.sql
│   │
│   ├── frontend/
│   │   ├── index.html
│   │   ├── app.js
│   │   └── styles.css
│   │
│   ├── Dockerfile
│   └── requirements.txt
│
├── helper_scripts/
│   ├── ec2_setup.sh
│   ├── git_setup.sh
│   └── push_changes.sh
│
└── terraform/
    ├── main.tf
    ├── outputs.tf
    └── variables.tf
```

## Prerequisites

**Required**
- Python 3.8+ (3.12 recommended)
- pip
- Git
- SQLite

**For production deployment**
- AWS account
- Terraform v1.0+
- Ansible v2.9+
- AWS CLI configured with credentials
- SSH key pair for EC2 access

## Installation

### Local development

Clone the repository:
```bash
git clone https://github.com/mdhake1-dbs/FamilyTree.git
cd FamilyTree
```

Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

Install dependencies:
```bash
cd app
pip install -r requirements.txt
```

Initialize the database:
```bash
cd db
sqlite3 familytree.db < 01_schema_sqlite.sql
```

Configure the application by creating `.env` in `app/backend/`:
```env
FLASK_APP=backend.main
FLASK_ENV=development
SECRET_KEY=your-secret-key-here
JWT_SECRET_KEY=your-jwt-secret-here
DATABASE_URI=sqlite:///familytree.db
CORS_ORIGINS=http://localhost:3000,http://localhost:5000
```

Run the backend:
```bash
cd app/backend
python main.py
```

The API will be available at `http://localhost:5000`.

In a separate terminal, serve the frontend:
```bash
cd app/frontend
python -m http.server 8000
```

Access the application at `http://localhost:8000`.

### Production deployment

**Step 1: Provision infrastructure with Terraform**

```bash
cd terraform
terraform init
terraform plan
terraform apply
```

This creates an EC2 instance with security groups, IAM roles, and network configuration. Note the output values (EC2 public IP and instance ID).

**Step 2: Configure server with Ansible**

Update `ansible/hosts.ini` with the EC2 IP from Terraform output:
```bash
cd ../ansible
nano hosts.ini
```

Test connectivity and run the playbook:
```bash
ansible all -i hosts.ini -m ping
ansible-playbook -i hosts.ini playbook.yml
```

This installs system dependencies, application code, and sets up the systemd service.

**Step 3: Deploy with Docker (alternative)**

SSH into the EC2 instance:
```bash
ssh -i your-key.pem ubuntu@<ec2-public-ip>
```

Clone and build:
```bash
git clone https://github.com/mdhake1-dbs/FamilyTree.git
cd FamilyTree/app
docker build -t familytree .
docker run -d -p 5000:5000 --name familytree familytree
```

Verify deployment:
```bash
sudo systemctl status familytree
curl http://<ec2-public-ip>:5000/api/health
```

## Usage

### Authentication

Register a new user:
```bash
curl -X POST http://localhost:5000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"user", "password":"pass", "email":"user@example.com"}'
```

Login:
```bash
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"user", "password":"pass"}'
```

### Managing people

Create a person:
```bash
curl -X POST http://localhost:5000/api/people \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"first_name":"John", "last_name":"Doe", "birth_date":"1980-01-01"}'
```

Get all people:
```bash
curl -X GET http://localhost:5000/api/people \
  -H "Authorization: Bearer <token>"
```

### Creating relationships

```bash
curl -X POST http://localhost:5000/api/relationships \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"person1_id":1, "person2_id":2, "relationship_type":"parent"}'
```

## API Endpoints

### Authentication
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Login
- `POST /api/auth/logout` - Logout (requires auth)
- `GET /api/auth/me` - Get current user (requires auth)

### People
- `GET /api/people` - List all people (requires auth)
- `GET /api/people/:id` - Get person by ID (requires auth)
- `POST /api/people` - Create new person (requires auth)
- `PUT /api/people/:id` - Update person (requires auth)
- `DELETE /api/people/:id` - Delete person (requires auth)

### Relationships
- `GET /api/relationships` - List all relationships (requires auth)
- `GET /api/relationships/:id` - Get relationship by ID (requires auth)
- `POST /api/relationships` - Create relationship (requires auth)
- `DELETE /api/relationships/:id` - Delete relationship (requires auth)

### Events
- `GET /api/events` - List all events (requires auth)
- `GET /api/events/:id` - Get event by ID (requires auth)
- `POST /api/events` - Create new event (requires auth)
- `PUT /api/events/:id` - Update event (requires auth)
- `DELETE /api/events/:id` - Delete event (requires auth)

### Misc
- `GET /api/health` - Health check
- `GET /api/export/gedcom` - Export as GEDCOM (requires auth)
- `GET /api/export/json` - Export as JSON (requires auth)

## Database Schema

The core tables are:

**users** - User accounts
```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

**people** - Individual family members
```sql
CREATE TABLE people (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    first_name TEXT NOT NULL,
    middle_name TEXT,
    last_name TEXT,
    birth_date DATE,
    death_date DATE,
    birth_place TEXT,
    death_place TEXT,
    gender TEXT,
    notes TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

**relationships** - Connections between people
```sql
CREATE TABLE relationships (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    person1_id INTEGER NOT NULL,
    person2_id INTEGER NOT NULL,
    relationship_type TEXT NOT NULL,
    start_date DATE,
    end_date DATE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (person1_id) REFERENCES people(id),
    FOREIGN KEY (person2_id) REFERENCES people(id)
);
```

**events** - Life events for individuals
```sql
CREATE TABLE events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    person_id INTEGER,
    event_type TEXT NOT NULL,
    event_date DATE,
    event_place TEXT,
    description TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (person_id) REFERENCES people(id)
);
```

## DevOps Reference

### Terraform commands
```bash
terraform init          # Initialize
terraform fmt           # Format files
terraform validate      # Validate configuration
terraform plan          # Preview changes
terraform apply         # Apply changes
terraform show          # Show current state
terraform state list    # List resources
terraform destroy       # Destroy infrastructure
```

### Ansible commands
```bash
ansible-playbook playbook.yml --syntax-check    # Check syntax
ansible-playbook -i hosts.ini playbook.yml --check    # Dry run
ansible-playbook -i hosts.ini playbook.yml -vvv       # Verbose output
ansible all -i hosts.ini -m ping                      # Test connectivity
```

### Docker commands
```bash
docker build -t familytree:latest .     # Build image
docker run -d -p 5000:5000 --name familytree familytree:latest    # Run
docker logs -f familytree               # View logs
docker exec -it familytree /bin/bash    # Execute commands
docker stop familytree                  # Stop container
docker rm familytree                    # Remove container
```

## Troubleshooting

**Database connection errors**

Check if the database file exists and has correct permissions:
```bash
ls -l app/db/familytree.db
chmod 664 app/db/familytree.db
```

Reinitialize if needed:
```bash
sqlite3 app/db/familytree.db < app/db/01_schema_sqlite.sql
```

**Port already in use**

Find and kill the process:
```bash
lsof -i :5000
kill -9 <PID>
```

**CORS errors**

- Verify Flask-CORS is installed
- Check CORS_ORIGINS in config.py
- Confirm the frontend is requesting the correct backend URL

**Authentication issues**

- Ensure JWT_SECRET_KEY is set in .env
- Check that the Authorization header includes the token
- Verify the token hasn't expired

## Documentation Resources

### Backend
- [Flask documentation](https://flask.palletsprojects.com/)
- [SQLite documentation](https://www.sqlite.org/docs.html)
- [PyJWT library](https://pyjwt.readthedocs.io/)
- [Flask-CORS](https://flask-cors.readthedocs.io/)

### Frontend
- [MDN JavaScript guide](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide)
- [Fetch API](https://developer.mozilla.org/en-US/docs/Web/API/Fetch_API)
- [DOM manipulation](https://developer.mozilla.org/en-US/docs/Web/API/Document_Object_Model)

### Infrastructure
- [Terraform documentation](https://developer.hashicorp.com/terraform/docs)
- [Ansible documentation](https://docs.ansible.com/)
- [Docker documentation](https://docs.docker.com/)
- [AWS EC2 documentation](https://docs.aws.amazon.com/ec2/)

## Contributing

Contributions are welcome. To contribute:

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Commit your changes: `git commit -m 'Add your feature'`
4. Push to the branch: `git push origin feature/your-feature`
5. Open a pull request

Follow PEP 8 for Python code and write tests for new features. Make sure all tests pass before submitting.

## Roadmap

- Multi-user support with granular permissions
- Mobile application (iOS/Android)
- Advanced search and filtering
- Photo recognition and tagging
- Integration with ancestry databases
- Enhanced timeline visualizations
- Real-time collaboration features
- Import from other genealogy tools

## License

This project is licensed under the MIT License.

## Acknowledgments

Thanks to the Flask, SQLite, Terraform, and Ansible communities, as well as AWS for infrastructure support and the open source genealogy projects that provided inspiration.
