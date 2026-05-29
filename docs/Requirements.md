# HR - Performance Evaluation Platform - Requirements

## Table of Contents

### Overview Documents
- [Business Problem](#business-problem)
- [Current State](#current-state)
- [Product Description](#product-description)
- [Personas](#personas)
- [Success Metrics](#success-metrics)
- [Technical Requirements](#technical-requirements)

### Feature Requirements
- [Authentication & Authorization](#authentication-authorization)
- [Evaluation Management](#evaluation-management)
- [Collaboration & Approval Workflow](#collaboration-approval-workflow)
- [Export & Import](#export-import)

---

# Overview Documents

## Business Problem

University of Waterloo's co-op program requires employers to provide structured, formal performance evaluations to students at the end of each work term. For organizations that hire several co-op students per term, managing this process internally creates real friction. Drafting evaluations, routing them to the right people for review, getting sign-off, and then submitting them to the university all require coordination that the evaluation form itself does not support.

The core problem is that the evaluation form and the internal collaboration process have never been unified in a single tool. Teams must work around this by passing annotated PDFs via email or converting evaluation content to plain text and sharing it through other channels. This introduces version confusion, increases administrative effort, and creates risk that evaluations are delayed, misfiled, or submitted without proper internal review.

## Current State

The current internal tool is a standalone HTML form with no server backend. It captures UW co-op evaluation data and stores drafts in the browser's local storage. For sharing, users export the evaluation as JSON and send the file to colleagues, who import it on their own machine to view or edit. A Markdown export feature helps users copy evaluation content into the official University of Waterloo co-op portal.

While this tool solved the immediate problem of capturing structured evaluation data, it was designed as a single-user utility, not a multi-user workflow system. There is no authentication, no role-based access control, no server-side persistence, and no mechanism for routing an evaluation through review and approval. All collaboration happens outside the tool — over email or messaging — and any state saved in local storage is invisible to other users and lost if the browser is cleared.

## Product Description

The Performance Evaluation Platform is a web-based enterprise HR application for managing UW co-op performance evaluations from creation to submission. It replaces the single-user HTML form with a multi-user system that supports the full lifecycle of an evaluation: creating and editing, saving drafts on the server, routing for internal review, collecting VP approval, and exporting for submission to the University of Waterloo.

Access is controlled by three roles — VP, Manager, and Employee — so that each user interacts with the system in a way appropriate to their function. The platform is intended for organizations that hire co-op students regularly and need a repeatable, auditable internal process in place of the current PDF-and-email approach.

## Personas

The **VP** manages both the platform and the evaluation process. They create and manage user accounts, assign roles, and assign co-op Employees to Managers. They have organization-wide visibility into all evaluations, review submissions from Managers, and provide final approval before evaluations are submitted to the University of Waterloo. They can return evaluations to Draft if corrections are needed.

The **Manager** is the primary author of performance evaluations. They supervise co-op students directly and are responsible for creating, editing, and submitting evaluations for the Employees assigned to them. They can only view and act on evaluations they created. They initiate the review process by submitting a completed draft for VP review.

The **Employee** represents a co-op student placed at the organization. They are the subject of the performance evaluations created by their assigned Manager. Their platform access is the most restricted of the three roles and will be defined as the product is implemented.

## Success Metrics

Success is measured primarily by whether the platform eliminates the coordination overhead of the current PDF-based process. Evaluations should be completed and submitted to the University of Waterloo on time without requiring email exchanges to share or route the document. The time Managers spend completing and routing evaluations should decrease relative to the previous process. All evaluations should pass through VP HR approval before submission. No evaluation data should be lost due to browser state issues or manual file management, as was a risk with the local-storage-based predecessor.

## Technical Requirements

All access to the platform requires authentication — no functionality is accessible without a valid session. Role-based access control enforces the four defined roles (Admin, VP HR, Manager, Employee) at the application level, server-side. The platform is accessible via web browser with no client-side installation required. Evaluation data is persisted server-side, not in browser local storage.

# Feature Requirements

## Authentication & Authorization

## Overview

The Authentication & Authorization feature controls who can access the platform and what each user is permitted to do. All users must authenticate before accessing any part of the system. Three roles — VP, Manager, and Employee — determine the actions each user can take throughout the platform.

## Terminology

* **Role**: A named set of permissions assigned to a user account that determines what actions they can perform.
* **RBAC**: Role-Based Access Control — permissions are granted based on a user's assigned role, not configured individually per user.
* **Session**: An authenticated state established after a successful login that persists for a defined period.

## Requirements

### REQ-AUTH-001: User Login

**User Story:** As a user, I want to log in with my credentials, so that I can access the platform.

**Acceptance Criteria:**

* **AC-AUTH-001.1:** When a user submits valid credentials, the system shall grant access and establish an authenticated session.
* **AC-AUTH-001.2:** When a user submits invalid credentials, the system shall deny access and display an error message.
* **AC-AUTH-001.3:** When a user's session expires, the system shall require re-authentication before allowing further access.

### REQ-AUTH-002: User Account Management

**User Story:** As a VP, I want to create, edit, and deactivate user accounts, so that I can control who has access to the platform.

**Acceptance Criteria:**

* **AC-AUTH-002.1:** When a VP creates a user account, the system shall require a name, email address, and role.
* **AC-AUTH-002.2:** When a VP deactivates a user account, the system shall prevent that user from logging in.
* **AC-AUTH-002.3:** When a deactivated user attempts to log in, the system shall deny access.
* **AC-AUTH-002.4:** When a VP edits a user account, the system shall allow updating the user's name, email, and role.

### REQ-AUTH-003: Role Assignment

**User Story:** As a VP, I want to assign a role to each user account, so that each user has the appropriate level of access.

**Acceptance Criteria:**

* **AC-AUTH-003.1:** When a VP creates or edits a user account, the system shall require selection of exactly one role from: VP, Manager, Employee.
* **AC-AUTH-003.2:** When a user's role is changed, the system shall enforce the updated permissions on their next request.

### REQ-AUTH-004: Role-Based Access Enforcement

**User Story:** As a VP, I want all platform features and data to be access-controlled by role, so that users can only perform actions their role permits.

**Acceptance Criteria:**

* **AC-AUTH-004.1:** When a user attempts an action not permitted by their role, the system shall deny the action.
* **AC-AUTH-004.2:** The system shall enforce role permissions server-side on all data access and actions.

### REQ-AUTH-005: Employee-Manager Assignment

**User Story:** As a VP, I want to assign co-op Employees to a Manager, so that the Manager can create evaluations for their assigned students.

**Acceptance Criteria:**

* **AC-AUTH-005.1:** When a VP assigns an Employee to a Manager, the system shall record the assignment and permit that Manager to create evaluations for that Employee.
* **AC-AUTH-005.2:** When a VP removes an Employee assignment from a Manager, the system shall prevent the Manager from creating new evaluations for that Employee.
* **AC-AUTH-005.3:** When a Manager attempts to create an evaluation for an Employee not assigned to them, the system shall deny the action.

### REQ-AUTH-006: Manager Access Scope

**User Story:** As a Manager, I want my access scoped to my own evaluations and assigned Employees, so that I cannot view or act on data outside my responsibility.

**Acceptance Criteria:**

* **AC-AUTH-006.1:** When a Manager views the evaluations list, the system shall display only evaluations that the Manager created.
* **AC-AUTH-006.2:** When a Manager attempts to access an evaluation they did not create, the system shall deny access.
* **AC-AUTH-006.3:** When a Manager selects an Employee to evaluate, the system shall display only Employees assigned to that Manager.

## Feature Behavior & Rules

All routes and API endpoints require an authenticated session. Role permissions are enforced server-side and cannot be bypassed through client-side manipulation. A VP cannot deactivate their own account. Each user holds exactly one role at a time. The three roles have distinct scopes: VP manages user accounts, assigns co-op Employees to Managers, and has full visibility and approval rights over all evaluations; Manager creates and submits evaluations only for their assigned Employees and can only view evaluations they own; Employee has the most restricted access in the system.

## Evaluation Management

## Overview

Evaluation Management is the core function of the platform. It allows Managers to create UW co-op performance evaluations for the students they supervise, save drafts at any point, and manage their evaluations through the review and approval lifecycle. Evaluations are persisted server-side, eliminating reliance on browser state.

## Terminology

* **Evaluation**: A formal performance assessment completed by a Manager for a co-op student, structured according to the University of Waterloo co-op evaluation format.
* **Draft**: An evaluation that has been saved but not yet submitted for review or approval.

## Requirements

### REQ-EVAL-001: Create Evaluation

**User Story:** As a Manager, I want to create a new performance evaluation for a co-op student, so that I can document their performance for the term.

**Acceptance Criteria:**

* **AC-EVAL-001.1:** When a Manager creates a new evaluation, the system shall create an evaluation record associated with that Manager's account.
* **AC-EVAL-001.2:** When an evaluation is created, the system shall present the UW co-op evaluation form fields for the Manager to complete.
* **AC-EVAL-001.3:** When a new evaluation is created, the system shall set its initial state to Draft.

### REQ-EVAL-002: Save Draft

**User Story:** As a Manager, I want to save an evaluation as a draft, so that I can return to it and continue editing later.

**Acceptance Criteria:**

* **AC-EVAL-002.1:** When a Manager saves a draft, the system shall persist the current state of all evaluation fields server-side.
* **AC-EVAL-002.2:** When a Manager opens a saved draft, the system shall restore all previously entered field values.
* **AC-EVAL-002.3:** When a draft is saved, the system shall not advance the evaluation in the workflow.

### REQ-EVAL-003: Edit Evaluation

**User Story:** As a Manager, I want to edit an evaluation I created that is in Draft state, so that I can update the content before submitting it for review.

**Acceptance Criteria:**

* **AC-EVAL-003.1:** When a Manager opens an evaluation they own that is in Draft state, the system shall allow editing of all form fields.
* **AC-EVAL-003.2:** When a Manager attempts to edit an evaluation that is not in Draft state, the system shall prevent editing.

### REQ-EVAL-004: View Evaluations

**User Story:** As a Manager, I want to view all evaluations I have created, so that I can track their content and current status.

**Acceptance Criteria:**

* **AC-EVAL-004.1:** When a Manager views the evaluations list, the system shall display all evaluations they own with their current workflow state.

### REQ-EVAL-005: VP Evaluation Visibility

**User Story:** As a VP, I want to view all evaluations in the system, so that I can monitor the process and review submissions.

**Acceptance Criteria:**

* **AC-EVAL-005.1:** When a VP views the evaluations list, the system shall display all evaluations across all Managers and their current workflow states.

## Feature Behavior & Rules

Evaluations are owned by the Manager who created them. Only the owning Manager can edit an evaluation in Draft state. VP can view any evaluation but cannot edit evaluation content. A Manager can only view and act on evaluations they created, and can only create evaluations for Employees assigned to them by a VP. Draft evaluations are stored server-side and are not tied to browser state.

## Collaboration & Approval Workflow

## Overview

The Collaboration & Approval Workflow feature routes evaluations through an internal review and approval process before they are submitted to the University of Waterloo. It replaces the current practice of emailing PDFs or JSON files between colleagues by giving evaluations a defined lifecycle — Draft, In Review, and Approved — that all stakeholders can see and act on within the platform.

## Terminology

* **Workflow State**: The current stage of an evaluation in the review and approval process. Valid states are: Draft, In Review, and Approved.
* **Approval**: A formal sign-off by a VP indicating that an evaluation is ready for submission to the University of Waterloo.

## Requirements

### REQ-COLLAB-001: Submit for Review

**User Story:** As a Manager, I want to submit a completed evaluation for internal review, so that it can be reviewed and approved by VP before submission to the university.

**Acceptance Criteria:**

* **AC-COLLAB-001.1:** When a Manager submits a Draft evaluation for review, the system shall transition the evaluation's state to In Review.
* **AC-COLLAB-001.2:** When an evaluation is In Review, the system shall make it visible and accessible to VP users.
* **AC-COLLAB-001.3:** When an evaluation is In Review, the system shall prevent the owning Manager from editing the content.

### REQ-COLLAB-002: Return Evaluation to Draft

**User Story:** As a VP, I want to return an evaluation to Draft, so that the Manager can make corrections before resubmitting.

**Acceptance Criteria:**

* **AC-COLLAB-002.1:** When a VP returns an In Review evaluation to Draft, the system shall transition the evaluation's state back to Draft.
* **AC-COLLAB-002.2:** When an evaluation is returned to Draft, the system shall allow the owning Manager to edit it again.

### REQ-COLLAB-003: Approve Evaluation

**User Story:** As a VP, I want to approve an evaluation, so that it is marked as ready for submission to the University of Waterloo.

**Acceptance Criteria:**

* **AC-COLLAB-003.1:** When a VP approves an In Review evaluation, the system shall transition the evaluation's state to Approved.
* **AC-COLLAB-003.2:** When an evaluation is Approved, the system shall prevent editing by any user.

## Feature Behavior & Rules

The evaluation workflow follows a linear progression: Draft → In Review → Approved. A Manager can only submit an evaluation that is in Draft state. Only a VP can approve an evaluation or return it to Draft. An Approved evaluation is locked — no edits are permitted by any role. If an Approved evaluation requires revision, a VP must return it to Draft first. The Admin role has no participation in the evaluation workflow.

## Export & Import

## Overview

The Export & Import feature allows evaluation data to be moved in and out of the platform in formats suited for different purposes. Markdown export supports submission to the University of Waterloo's official co-op portal. JSON export and import support migration from the previous tool and structured data sharing.

## Terminology

* **Markdown Export**: An export of evaluation content formatted as Markdown, structured to match the University of Waterloo co-op evaluation form for use in the official portal.
* **PDF Export**: A printable export of evaluation content with the same fields as the Markdown export.

## Requirements

### REQ-EXPORT-001: Export Evaluation as Markdown

**User Story:** As a Manager, I want to export an evaluation as Markdown, so that I can use it to complete the official UW co-op evaluation form.

**Acceptance Criteria:**

* **AC-EXPORT-001.1:** When a Manager exports an evaluation as Markdown, the system shall generate a Markdown-formatted file containing all evaluation fields and their values.
* **AC-EXPORT-001.2:** When generating the Markdown export, the system shall structure the output to match the University of Waterloo co-op evaluation form format.

### REQ-EXPORT-002: Export Evaluation as PDF

**User Story:** As a Manager, I want to export an evaluation as a PDF, so that I can share or archive a printable copy of a draft or finalized evaluation.

**Acceptance Criteria:**

* **AC-EXPORT-002.1:** When a Manager exports an evaluation as PDF, the system shall generate a PDF file containing all evaluation fields and their values.
* **AC-EXPORT-002.2:** When generating the PDF export, the system shall include the same evaluation content as the Markdown export in a readable printable layout.

## Feature Behavior & Rules

Export is available on any evaluation regardless of its current workflow state. Import always creates a new Draft evaluation — it never overwrites an existing record. The Markdown export format corresponds to the University of Waterloo co-op evaluation portal structure. PDF export provides a printable copy with the same evaluation content. JSON export and import use the same schema, ensuring that a file exported from this platform can be re-imported without modification.
