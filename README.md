# FamilyTree Vault

Family Tree Valt is an Application aimed for families to preserve their history. It not only stores details about Blood relations but also about your friends, or any other person you come accross. 

## Features

As part of initial Development following Features are provided.

Each User can create own login.
You can add peoples along with their Short Biography.
Add Realtionships if exists between 2 persons.
Add any events for any person.

### Future Deliveries

Create a Document Vault to store important documents related to person's Identity.
A System to store crucial information which needs to be pass on to any person in the family in case of any tragedy.
Create a report from all the data to have a complete picture of a life of any person.
 
### Data management
- Currently all the data is managed using Sqlite3 Database

### Privacy and security
- Self-hosted deployment with complete data control
- Access control for viewing and editing permissions
- Audit logging for all modifications

## Technology Stack

**Frontend**
- HTML5, CSS3, JavaScript

**Backend**
- Python 3.12
- Flask 2.0+
- SQLite

**Infrastructure**
- Terraform for AWS EC2 provisioning
- Ansible for configuration management
- Docker for containerization
- GitHub Actions for CI/CD

## API Endpoints

### Authentication
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Login
- `POST /api/auth/logout` - Logout (requires auth)
- `GET /api/auth/me` - Get current user (requires auth)
- `PUT /api/auth/me` - Update current user (requires auth)

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
- `PUT /api/relationships/:id` - Update relationship (requires auth)
- `DELETE /api/relationships/:id` - Delete relationship (requires auth)

### Events
- `GET /api/events` - List all events (requires auth)
- `GET /api/events/:id` - Get event by ID (requires auth)
- `POST /api/events` - Create new event (requires auth)
- `PUT /api/events/:id` - Update event (requires auth)
- `DELETE /api/events/:id` - Delete event (requires auth)

### Misc
- `GET /api/health` - Health check

## Documentation Resources

### Backend
- [Flask and CORS Usage for Python API](https://flask-cors.readthedocs.io/en/latest/api.html)
- [SQLite Connection in Python](https://docs.python.org/3/library/sqlite3.html)
- [Password SHA256 hash in Python](https://docs.python.org/3/library/hashlib.html)

### Frontend
- [Javascript Event Listeners](https://www.w3schools.com/JS/js_htmldom_eventlistener.asp)
- [JavaScript HTML DOM Elements](https://www.w3schools.com/JS/js_htmldom_elements.asp)
- [JavaScript Fetch API](https://developer.mozilla.org/en-US/docs/Web/API/Fetch_API/Using_Fetch)
- [Use Session Storage tokens for Authentication in JS] (https://developer.mozilla.org/en-US/docs/Web/API/Window/sessionStorage)


### Infrastructure
- [Self Git Repository for Infrastructure Setup](https://github.com/mdhake1-dbs/network-sys-assessment)

### AI Usage
- ChatGPT for Code Realignment (https://chatgpt.com/share/69414d25-0cc4-8001-8863-6584c5ee3c8f) 
- ChatGPT for frontend changes and modifications (https://chatgpt.com/share/69414dbb-9a84-8001-8182-a6e95074051c)


## Acknowledgments

Thanks to the Flask, SQLite, Terraform, and Ansible communities, as well as AWS for infrastructure support and the open source genealogy projects that provided inspiration.
