<!--
Sync Impact Report:
- Version change: initial → 1.0.0
- Modified principles: N/A (initial version)
- Added sections: 
  * Core Principles (5 principles: Code Quality, Testing Discipline, User Experience, Performance Optimization, Deployment Strategy)
  * Development Workflow
  * Governance
- Removed sections: N/A
- Templates requiring updates:
  ✅ plan-template.md - Constitution Check section aligns with new principles
  ✅ spec-template.md - Requirements section supports quality and testing principles
  ✅ tasks-template.md - Task categorization reflects testing and performance principles
- Follow-up TODOs: None
-->

# MyStock Constitution

## Core Principles

### I. Code Quality (NON-NEGOTIABLE)

All code MUST be concise, readable, and maintainable. Comments are REQUIRED at the function level and MUST be brief and focused on purpose, not implementation details.

**Rules**:
- Function comments MUST describe what the function does and its purpose
- Complex logic MUST have inline comments explaining the "why", not the "how"
- Variable and function names MUST be self-documenting
- Code duplication MUST be avoided through proper abstraction
- Code reviews MUST verify readability and comment quality

**Rationale**: Clear code reduces maintenance burden, accelerates onboarding, and prevents technical debt accumulation in a stock trading application where correctness is critical.

### II. Testing Discipline (NON-NEGOTIABLE)

External API calls MUST be rate-limited and tested with MAXIMUM one successful execution per test run to prevent API blocking and quota exhaustion.

**Rules**:
- Tests that call external APIs MUST verify connectivity with a single request only
- Mock or stub external dependencies for repeated test executions
- Integration tests with external APIs MUST have retry logic with exponential backoff
- Test suites MUST NOT hammer external services during CI/CD runs
- Failed API tests MUST provide clear diagnostics without retrying automatically

**Rationale**: Stock market APIs often have strict rate limits. Excessive requests can lead to account suspension, blocking development and deployment pipelines.

### III. User Experience (NON-NEGOTIABLE)

The interface MUST be intuitive and responsive. Users MUST be able to complete core tasks without training or documentation.

**Rules**:
- Response time for user interactions MUST be under 200ms for local operations
- Loading states MUST be shown for operations exceeding 100ms
- Error messages MUST be user-friendly and actionable
- UI/UX changes MUST be validated with usability testing
- Interface complexity MUST be justified with user value

**Rationale**: Trading decisions are time-sensitive. Slow or confusing interfaces can result in missed opportunities or costly errors.

### IV. Performance Optimization (NON-NEGOTIABLE)

Code MUST use minimal dependencies. Every library added to the project MUST be justified by clear necessity and lack of simpler alternatives.

**Rules**:
- New dependencies MUST be approved with documented justification
- Standard library solutions MUST be preferred over third-party packages
- Dependency count MUST be tracked and reviewed quarterly
- Bundle size and startup time MUST be measured and optimized
- Heavy dependencies MUST be lazy-loaded or made optional

**Rationale**: Excessive dependencies increase attack surface, maintenance burden, deployment size, and startup time—all critical factors for a cloud-deployed financial application.

### V. Deployment Strategy

The application MUST be designed for deployment to Azure cloud services. All architectural decisions MUST consider Azure infrastructure capabilities and limitations.

**Rules**:
- Services MUST be containerizable or compatible with Azure App Service
- Configuration MUST use Azure Key Vault for secrets
- Logging MUST integrate with Azure Monitor or Application Insights
- Cost optimization MUST be considered in architecture decisions
- Disaster recovery and backup strategies MUST be documented

**Rationale**: Azure deployment is the target environment. Early alignment prevents costly refactoring and ensures optimal use of cloud capabilities.

## Development Workflow

### Code Review Requirements
- All code changes MUST pass peer review
- Reviews MUST verify compliance with all five core principles
- Reviewers MUST validate comment quality and code readability
- Dependency additions MUST be explicitly approved in review

### Testing Gates
- All PRs MUST pass automated test suites
- Tests with external APIs MUST demonstrate rate-limit compliance
- Performance regressions MUST block PR approval
- Test coverage MUST be maintained or improved

### Azure Deployment Checklist
- Configuration MUST be externalized and cloud-ready
- Secrets MUST NOT be committed to repository
- Application MUST be tested in Azure staging environment before production
- Rollback procedures MUST be documented and tested

## Governance

This constitution supersedes all other development practices and guidelines. All team members MUST adhere to these principles without exception unless an amendment is formally approved.

### Amendment Process
1. Proposed changes MUST be documented with rationale
2. Changes MUST be reviewed by all team members
3. Approved amendments MUST update this document with incremented version
4. Migration plan MUST be created for breaking changes

### Compliance Verification
- All PRs and code reviews MUST verify constitutional compliance
- Violations MUST be documented with justification or corrected
- Quarterly audits MUST assess adherence to principles
- Persistent violations MUST trigger process review

### Version Control
- Version follows MAJOR.MINOR.PATCH semantic versioning
- MAJOR: Backward-incompatible principle changes or removals
- MINOR: New principles added or material expansions
- PATCH: Clarifications, wording improvements, typo fixes

**Version**: 1.0.0 | **Ratified**: 2025-10-20 | **Last Amended**: 2025-10-20
