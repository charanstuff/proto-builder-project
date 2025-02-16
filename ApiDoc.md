# Authentication & Access Control
These endpoints handle user accounts, roles, and secure session/token workflows.

## Auth Endpoints
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /auth/register | Register a new user. |
| POST | /auth/login | Authenticate with email/username & password, returns token (JWT). |
| GET | /auth/me | Get current user info (based on token). |
| POST | /auth/logout | Invalidate current token (if implementing server-side token store). |

### Request/Response Examples
POST /auth/login

Request Body:json
{
  "email": "user@example.com",
  "password": "MySecret123"
}

Response:
json
{
  "token": "jwt-token-here",
  "user": {
    "id": 123,
    "email": "user@example.com",
    "role": "Admin"
  }
}

## User & Role Management (Optional / Admin)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /users | List all users (admin only). |
| GET | /users/:userId | Get detailed info for a single user. |
| PATCH | /users/:userId | Update user info or role (e.g., SalesRep, Manager, Admin). |
| DELETE | /users/:userId | Remove or deactivate a user (admin only). |

# Data & Campaign Manager
Handles all CRUD operations for leads and campaigns, plus attaching leads to campaigns.

## Leads
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /leads | List/query leads (supports filters, pagination). |
| POST | /leads | Bulk or single lead creation (e.g., CSV upload). |
| GET | /leads/:leadId | Retrieve details of a specific lead (incl. status, score, conversation logs if needed). |
| PATCH | /leads/:leadId | Update lead info (e.g., classification override, contact details). |
| DELETE | /leads/:leadId | Delete or archive a lead. (Be cautious with data retention policies.) |

### CSV Upload Workflow
POST /leads with Content-Type: multipart/form-data or JSON containing an array of leads.
Each lead is stored with fields like name, email, company, etc.

## Campaigns
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /campaigns | List all campaigns (optionally filtered by status: "active," "paused," "completed"). |
| POST | /campaigns | Create a new campaign (name, subject line, etc.). |
| GET | /campaigns/:campId | Retrieve campaign details (metadata, lead list, status). |
| PATCH | /campaigns/:campId | Update campaign fields (e.g., name, status, follow-up intervals). |
| DELETE | /campaigns/:campId | Delete or archive an existing campaign. |
| POST | /campaigns/:campId/leads | Attach additional leads to a running campaign. |

### Launch / Pause / Resume
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /campaigns/:campId/launch | Start sending initial outreach if campaign is in draft. |
| POST | /campaigns/:campId/pause | Temporarily halt outreach/follow-ups. |
| POST | /campaigns/:campId/resume | Resume a paused campaign, continuing from last status. |

### Sample Body for Creating a Campaign
json
Copy
Edit
{
  "name": "My First Outreach",
  "subjectLine": "Hello from MyStartup",
  "followUpIntervalDays": 3,
  "leadIds": [101, 102, 103],
  "template": "Hi {{firstName}}, we noticed you..."
}

# LLM Manager
Typically, the LLM Manager is internal—the front-end doesn't call it directly. However, for testing or advanced admin configuration, you may expose specialized endpoints:
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /llm/testPrompt | Admin/testing endpoint: send a prompt to the currently configured LLM, get a raw response. |
| GET | /llm/providers | List available LLM providers and show which is currently active. |
| PATCH | /llm/providers | Switch the active provider or update credentials. |

Note: In normal usage, the Outreach or Product Context modules call the LLM Manager internally to generate emails, classify replies, etc.

# Outreach Engine & Follow-Up
Coordinates sending emails/messages and scheduling follow-ups.
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /campaigns/:campId/send | Immediately send the first wave of outreach (if not automatically triggered on launch). This can be used for manual triggered sends. |
| GET | /campaigns/:campId/leads/:leadId/conversation | Return the full conversation history for a specific lead in a campaign (AI messages + lead replies + manual messages). |
| POST | /campaigns/:campId/leads/:leadId/messages | Send a manual message to that lead (user override). The system records it in the conversation log and halts automated follow-ups unless "ceded." |
| POST | /campaigns/:campId/leads/:leadId/override | User forcibly takes control of the conversation for that lead, stopping the AI from sending further messages. |
| POST | /campaigns/:campId/leads/:leadId/cede | User cedes control back to the AI, letting it resume automated follow-up. The AI must read conversation logs to maintain context. |

Internal: A background job or cron handles scheduled follow-ups, calling the LLM manager for new messages.

# Scoring & Classification
Mostly triggered automatically by inbound replies or changes in lead data, but also supports manual override.
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /leads/:leadId | Includes fields like score, classification, qualificationStatus in the response. |
| PATCH | /leads/:leadId | Accepts manual updates to score or classification (e.g., override AI classification). |
| POST | /leads/:leadId/reclassify | Forces the system to re-run classification logic on a lead's latest messages (for debugging or updated criteria). |

Inbound Email Handling: If using inbound webhooks from the email provider, those will be internal routes (e.g., /webhook/email-inbound). On receiving a reply, the system calls the classification logic, updates score, sets classification, and notifies the user if threshold is reached.

# Analytics & Reporting
Exposes read-only endpoints to fetch campaign/lead performance data and export results.
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /campaigns/:campId/analytics | Returns aggregated stats: open rate, reply rate, qualified leads, etc. |
| GET | /campaigns/analytics | (Optionally) aggregated stats across all campaigns or for a date range. |
| GET | /campaigns/:campId/export | Generates a CSV or PDF with lead statuses, conversation snippets, and performance KPIs. |

## Example Analytics Response:
json
Copy
Edit
{
  "campaignId": 45,
  "openRate": 0.48,
  "replyRate": 0.12,
  "qualifiedCount": 15,
  "totalLeads": 120,
  "startTime": "2025-02-01T10:00:00Z",
  "endTime": null
}

# Admin & Configuration
Provides system-wide configuration endpoints, including email settings, environment toggles, or any advanced options.
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /admin/config | View current system config (LLM provider, email service, lead scoring parameters). |
| PATCH | /admin/config | Update configuration fields (e.g., set new email API key, scoring formula). |
| GET | /admin/health | Quick health check (e.g., verifying DB & LLM connectivity). |

Note: Alternatively, you might have separate endpoints for each config domain (e.g., /admin/llm, /admin/email, etc.).

# Product Context & Use-Case Definition
Implements the chat interface for describing a product, storing that info as metadata, and applying it to lead searches.
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /productContext | Retrieves the current stored metadata about the user's product, target industries, etc. |
| POST | /productContext/chat | Accepts user messages describing the product; system may respond with clarifying questions or confirmations. |
| GET | /productContext/log | Lists the entire conversation history around product context, if needed for auditing. |
| GET | /productContext/recommendations | (Optional) Suggest new leads or industries based on stored metadata. |

## Sample Workflow:
POST /productContext/chat with JSON body like:
json
Copy
Edit
{
  "userMessage": "We pivoted to focusing on automotive supply chain SaaS..."
}
System updates the productContext metadata and returns a system message acknowledging or asking for more detail.

# Usage Notes

## Authentication:
Most endpoints require a valid JWT token in the Authorization header (e.g., Bearer <token>).

## Access Control:
Some endpoints (e.g., /users, /admin/*) are Admin only.
Others (e.g., /campaigns, /leads) are for general Sales Rep or Manager roles.

## Scalability:
Calls that trigger large-scale operations (e.g., mass emails) should be asynchronous with background jobs.

## Error Handling:
Return standard HTTP error codes (4xx for client errors, 5xx for server errors), with JSON error messages.

# Final Thoughts

This API set covers:
- Authentication & Role Management
- Lead Ingestion, Updates, & Deletion
- Campaign Management (including adding/removing leads, pausing, resuming)
- LLM Integration (test endpoints + internal usage)
- Outreach & Follow-up (manual override, ceding control)
- Scoring & Classification (automatic + manual override)
- Analytics & Reporting (per-campaign or global)
- Admin Configuration (LLM/email settings, environment toggles)
- Product Context Chat (persisting metadata, potential recommendations)
