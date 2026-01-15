"""
Gatekeeper Agent - Security and Access Control

The Gatekeeper enforces Role-Based Access Control (RBAC) and maintains
audit trails for all sensitive operations.

Responsibilities:
- Implement and enforce RBAC policies
- Ensure data privacy (peers only see what they should)
- Audit logging for all access and modifications
- PII protection and redaction
- Access request approval workflows
- Compliance reporting

Design Pattern: Policy-Based Access Control + Audit Chain
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set
from uuid import UUID, uuid4

from loguru import logger

from iras.core.agent import Agent, AgentConfig, AgentTool
from iras.core.memory import MemoryType
from iras.core.reasoning import EvidenceType
from iras.core.state import AgentStatus
from iras.databases.document_store import DocumentStore


class Role(str, Enum):
    """User roles in the system"""

    EMPLOYEE = "employee"  # Can see own evaluation, submit feedback
    MANAGER = "manager"  # Can see direct reports, write evaluations
    HR_ADMIN = "hr_admin"  # Can see all evaluations, manage cycles
    SYSTEM_ADMIN = "system_admin"  # Full access
    PEER_REVIEWER = "peer_reviewer"  # Can submit peer feedback


class Permission(str, Enum):
    """Granular permissions"""

    # Read permissions
    READ_OWN_EVALUATION = "read_own_evaluation"
    READ_DIRECT_REPORT_EVALUATION = "read_direct_report_evaluation"
    READ_ALL_EVALUATIONS = "read_all_evaluations"
    READ_PEER_FEEDBACK = "read_peer_feedback"

    # Write permissions
    WRITE_SELF_EVAL = "write_self_eval"
    WRITE_PEER_FEEDBACK = "write_peer_feedback"
    WRITE_MANAGER_EVALUATION = "write_manager_evaluation"

    # Admin permissions
    MANAGE_CYCLES = "manage_cycles"
    MANAGE_USERS = "manage_users"
    VIEW_AUDIT_LOGS = "view_audit_logs"
    EXPORT_DATA = "export_data"


class AccessDecision(str, Enum):
    """Access control decision"""

    ALLOW = "allow"
    DENY = "deny"
    REDACT = "redact"  # Allow but redact sensitive fields


class AuditAction(str, Enum):
    """Types of auditable actions"""

    READ = "read"
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    EXPORT = "export"
    ACCESS_DENIED = "access_denied"


class AuditLog:
    """Audit log entry"""

    def __init__(
        self,
        actor_id: UUID,
        action: AuditAction,
        resource_type: str,
        resource_id: UUID,
        decision: AccessDecision,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        self.id = uuid4()
        self.actor_id = actor_id
        self.action = action
        self.resource_type = resource_type
        self.resource_id = resource_id
        self.decision = decision
        self.metadata = metadata or {}
        self.timestamp = datetime.now()


class Gatekeeper(Agent):
    """
    Security and access control agent

    The Gatekeeper is the guardian of data privacy and security,
    ensuring that users only access what they're authorized to see.

    Capabilities:
    - Role-Based Access Control (RBAC)
    - Data privacy enforcement
    - PII redaction
    - Audit logging
    - Access request management
    - Compliance reporting
    """

    def __init__(
        self,
        name: str = "Gatekeeper",
        document_store: Optional[DocumentStore] = None,
    ):
        config = AgentConfig(
            name=name,
            role="security",
            capabilities={
                "rbac_enforcement",
                "audit_logging",
                "pii_protection",
                "access_control",
                "compliance_reporting",
            },
            temperature=0.0,  # Deterministic for security
            max_tokens=2000,
            autonomous_mode=False,  # Require explicit authorization
        )
        super().__init__(config)

        # Database connection
        self.document_store = document_store or DocumentStore()

        # RBAC policy definitions
        self.role_permissions: Dict[Role, Set[Permission]] = self._initialize_rbac_policies()

        # Sensitive fields that should be redacted
        self.sensitive_fields = {
            "raw_input",  # Raw feedback before synthesis
            "personal_notes",  # Manager's private notes
            "salary_info",  # Compensation data
            "medical_info",  # Health information
        }

        # Audit log cache (write to DB periodically)
        self.audit_cache: List[AuditLog] = []

        # Register tools
        self._register_security_tools()

        logger.info(f"Gatekeeper '{name}' initialized with {len(self.role_permissions)} roles")

    def _initialize_rbac_policies(self) -> Dict[Role, Set[Permission]]:
        """Initialize role-permission mappings"""
        policies = {
            Role.EMPLOYEE: {
                Permission.READ_OWN_EVALUATION,
                Permission.WRITE_SELF_EVAL,
                Permission.WRITE_PEER_FEEDBACK,
                Permission.READ_PEER_FEEDBACK,  # Only their own submitted feedback
            },
            Role.MANAGER: {
                Permission.READ_OWN_EVALUATION,
                Permission.READ_DIRECT_REPORT_EVALUATION,
                Permission.WRITE_SELF_EVAL,
                Permission.WRITE_PEER_FEEDBACK,
                Permission.WRITE_MANAGER_EVALUATION,
                Permission.READ_PEER_FEEDBACK,
            },
            Role.HR_ADMIN: {
                Permission.READ_ALL_EVALUATIONS,
                Permission.READ_PEER_FEEDBACK,
                Permission.MANAGE_CYCLES,
                Permission.VIEW_AUDIT_LOGS,
                Permission.EXPORT_DATA,
            },
            Role.SYSTEM_ADMIN: set(Permission),  # All permissions
            Role.PEER_REVIEWER: {
                Permission.WRITE_PEER_FEEDBACK,
                Permission.READ_PEER_FEEDBACK,  # Only their own
            },
        }

        return policies

    def _register_security_tools(self) -> None:
        """Register Gatekeeper-specific tools"""
        self.register_tool(
            AgentTool(
                name="check_access",
                description="Check if user has access to resource",
                parameters={
                    "user_id": {"type": "string"},
                    "resource_type": {"type": "string"},
                    "resource_id": {"type": "string"},
                    "action": {"type": "string"},
                },
                function=self.check_access,
            )
        )

        self.register_tool(
            AgentTool(
                name="audit_log",
                description="Log an auditable action",
                parameters={
                    "actor_id": {"type": "string"},
                    "action": {"type": "string"},
                    "resource_type": {"type": "string"},
                    "resource_id": {"type": "string"},
                },
                function=self.audit_log,
            )
        )

        self.register_tool(
            AgentTool(
                name="redact_sensitive_data",
                description="Redact sensitive fields from document",
                parameters={
                    "document": {"type": "object"},
                    "user_role": {"type": "string"},
                },
                function=self.redact_sensitive_data,
            )
        )

    async def check_access(
        self,
        user_id: UUID,
        resource_type: str,
        resource_id: UUID,
        action: AuditAction,
    ) -> Dict[str, Any]:
        """
        Check if user has access to perform action on resource

        Args:
            user_id: User requesting access
            resource_type: Type of resource (evaluation, feedback, etc.)
            resource_id: Specific resource ID
            action: Action to perform (read, write, delete)

        Returns:
            Access decision with reasoning
        """
        await self.state_manager.update_status(
            AgentStatus.EXECUTING,
            reason=f"Checking access for user {user_id}",
        )

        try:
            # Load user to get roles
            user_doc = await self.document_store.find_by_id(
                collection="employees",
                doc_id=str(user_id),
            )

            if not user_doc:
                decision = AccessDecision.DENY
                reason = "User not found"
            else:
                # Get user roles (could have multiple)
                user_roles = user_doc.get("roles", [Role.EMPLOYEE.value])
                user_roles = [Role(r) for r in user_roles]

                # Check permissions
                decision, reason = await self._evaluate_access(
                    user_id=user_id,
                    user_roles=user_roles,
                    resource_type=resource_type,
                    resource_id=resource_id,
                    action=action,
                )

            # Log access check
            await self.audit_log(
                actor_id=user_id,
                action=AuditAction.ACCESS_DENIED if decision == AccessDecision.DENY else action,
                resource_type=resource_type,
                resource_id=resource_id,
                decision=decision,
                metadata={"reason": reason},
            )

            # Add to reasoning
            await self.reasoning.add_evidence(
                content=f"Access {decision.value} for user {user_id} on {resource_type}:{resource_id}",
                evidence_type=EvidenceType.FACTUAL,
                confidence=1.0,
                source=f"gatekeeper_{self.id}",
            )

            logger.info(
                f"Access check: {decision.value} - User {user_id} {action.value} {resource_type}:{resource_id}"
            )

            return {
                "decision": decision.value,
                "reason": reason,
                "user_id": str(user_id),
                "resource_type": resource_type,
                "resource_id": str(resource_id),
                "action": action.value,
                "timestamp": datetime.now().isoformat(),
            }

        finally:
            await self.state_manager.update_status(AgentStatus.IDLE)

    async def _evaluate_access(
        self,
        user_id: UUID,
        user_roles: List[Role],
        resource_type: str,
        resource_id: UUID,
        action: AuditAction,
    ) -> Tuple[AccessDecision, str]:
        """
        Evaluate access based on RBAC policies and context

        Returns:
            (decision, reason)
        """
        # Map action to required permission
        action_permission_map = {
            AuditAction.READ: self._get_read_permission(resource_type),
            AuditAction.CREATE: self._get_write_permission(resource_type),
            AuditAction.UPDATE: self._get_write_permission(resource_type),
            AuditAction.DELETE: Permission.MANAGE_CYCLES,  # Only admins
            AuditAction.EXPORT: Permission.EXPORT_DATA,
        }

        required_permission = action_permission_map.get(action)
        if not required_permission:
            return AccessDecision.DENY, f"Unknown action: {action}"

        # Check if any of user's roles have the required permission
        has_permission = False
        for role in user_roles:
            if required_permission in self.role_permissions.get(role, set()):
                has_permission = True
                break

        if not has_permission:
            return AccessDecision.DENY, f"Missing required permission: {required_permission.value}"

        # Additional context-based checks
        if resource_type == "evaluation":
            return await self._check_evaluation_access(user_id, resource_id, action)
        elif resource_type == "peer_feedback":
            return await self._check_feedback_access(user_id, resource_id, action)

        return AccessDecision.ALLOW, "Permission granted"

    async def _check_evaluation_access(
        self,
        user_id: UUID,
        eval_id: UUID,
        action: AuditAction,
    ) -> Tuple[AccessDecision, str]:
        """Check access to evaluation with context"""
        # Load evaluation
        eval_doc = await self.document_store.find_by_id(
            collection="evaluations",
            doc_id=str(eval_id),
        )

        if not eval_doc:
            return AccessDecision.DENY, "Evaluation not found"

        employee_id = UUID(eval_doc["employee_id"])
        manager_id = UUID(eval_doc["manager_id"])

        # Employee can read their own evaluation
        if action == AuditAction.READ and user_id == employee_id:
            return AccessDecision.ALLOW, "Employee accessing own evaluation"

        # Manager can read/write direct report evaluation
        if user_id == manager_id:
            return AccessDecision.ALLOW, "Manager accessing direct report evaluation"

        # Check if user is a peer reviewer
        approved_peers = [UUID(p) for p in eval_doc.get("manager_approved_peers", [])]
        if user_id in approved_peers:
            if action == AuditAction.READ:
                return AccessDecision.REDACT, "Peer reviewer - limited access"
            else:
                return AccessDecision.DENY, "Peers can only submit feedback"

        return AccessDecision.DENY, "No relationship to evaluation"

    async def _check_feedback_access(
        self,
        user_id: UUID,
        feedback_id: UUID,
        action: AuditAction,
    ) -> Tuple[AccessDecision, str]:
        """Check access to peer feedback"""
        # Load feedback
        feedback_doc = await self.document_store.find_by_id(
            collection="peer_feedbacks",
            doc_id=str(feedback_id),
        )

        if not feedback_doc:
            return AccessDecision.DENY, "Feedback not found"

        peer_id = UUID(feedback_doc["peer_id"])

        # Peer who wrote it can read their own feedback
        if user_id == peer_id:
            return AccessDecision.ALLOW, "Accessing own feedback"

        # Load evaluation to check if user is manager
        eval_id = UUID(feedback_doc["evaluation_id"])
        eval_doc = await self.document_store.find_by_id(
            collection="evaluations",
            doc_id=str(eval_id),
        )

        if eval_doc and UUID(eval_doc["manager_id"]) == user_id:
            return AccessDecision.ALLOW, "Manager accessing peer feedback"

        return AccessDecision.DENY, "Not authorized to view this feedback"

    async def audit_log(
        self,
        actor_id: UUID,
        action: AuditAction,
        resource_type: str,
        resource_id: UUID,
        decision: AccessDecision = AccessDecision.ALLOW,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Log an auditable action

        Args:
            actor_id: User performing action
            action: Action performed
            resource_type: Type of resource
            resource_id: Resource ID
            decision: Access decision
            metadata: Additional context

        Returns:
            Audit log entry
        """
        audit_entry = AuditLog(
            actor_id=actor_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            decision=decision,
            metadata=metadata,
        )

        # Store in document store
        audit_dict = {
            "actor_id": str(actor_id),
            "action": action.value,
            "resource_type": resource_type,
            "resource_id": str(resource_id),
            "decision": decision.value,
            "metadata": metadata or {},
            "timestamp": audit_entry.timestamp.isoformat(),
        }

        await self.document_store.insert(
            collection="audit_logs",
            document=audit_dict,
            doc_id=str(audit_entry.id),
        )

        # Cache for in-memory tracking
        self.audit_cache.append(audit_entry)
        if len(self.audit_cache) > 1000:
            self.audit_cache = self.audit_cache[-1000:]  # Keep last 1000

        return {
            "audit_id": str(audit_entry.id),
            "logged_at": audit_entry.timestamp.isoformat(),
        }

    async def redact_sensitive_data(
        self,
        document: Dict[str, Any],
        user_role: Role,
    ) -> Dict[str, Any]:
        """
        Redact sensitive fields from document based on user role

        Args:
            document: Document to redact
            user_role: Role of user requesting data

        Returns:
            Redacted document
        """
        # System admin and HR admin see everything
        if user_role in [Role.SYSTEM_ADMIN, Role.HR_ADMIN]:
            return document

        redacted = document.copy()

        # Redact sensitive fields
        for field in self.sensitive_fields:
            if field in redacted:
                redacted[field] = "[REDACTED]"

        # Additional role-specific redactions
        if user_role == Role.PEER_REVIEWER:
            # Peers don't see other peer feedback
            if "peer_feedbacks" in redacted:
                redacted["peer_feedbacks"] = "[REDACTED - Peer feedback confidential]"

        if user_role == Role.EMPLOYEE:
            # Employees don't see manager's private notes
            if "manager_evaluation" in redacted:
                manager_eval = redacted["manager_evaluation"]
                if isinstance(manager_eval, dict):
                    manager_eval["ai_questions"] = "[REDACTED]"
                    manager_eval["manager_responses"] = "[REDACTED]"

        return redacted

    async def generate_compliance_report(
        self,
        start_date: datetime,
        end_date: datetime,
    ) -> Dict[str, Any]:
        """
        Generate compliance report for audit period

        Args:
            start_date: Report start date
            end_date: Report end date

        Returns:
            Compliance metrics
        """
        # Query audit logs
        audit_logs = await self.document_store.find(
            collection="audit_logs",
            query={
                "timestamp": {
                    "$gte": start_date.isoformat(),
                    "$lte": end_date.isoformat(),
                }
            },
        )

        # Analyze logs
        total_accesses = len(audit_logs)
        denied_accesses = sum(1 for log in audit_logs if log["decision"] == AccessDecision.DENY.value)
        unique_actors = len(set(log["actor_id"] for log in audit_logs))

        # Action breakdown
        action_breakdown = {}
        for log in audit_logs:
            action = log["action"]
            action_breakdown[action] = action_breakdown.get(action, 0) + 1

        report = {
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat(),
            },
            "total_accesses": total_accesses,
            "denied_accesses": denied_accesses,
            "unique_users": unique_actors,
            "action_breakdown": action_breakdown,
            "denial_rate": denied_accesses / total_accesses if total_accesses > 0 else 0,
            "generated_at": datetime.now().isoformat(),
        }

        logger.info(
            f"Compliance report generated: {total_accesses} accesses, "
            f"{denied_accesses} denied ({report['denial_rate']:.1%})"
        )

        return report

    def _get_read_permission(self, resource_type: str) -> Permission:
        """Get appropriate read permission for resource type"""
        if resource_type == "evaluation":
            return Permission.READ_OWN_EVALUATION  # Most restrictive
        elif resource_type == "peer_feedback":
            return Permission.READ_PEER_FEEDBACK
        else:
            return Permission.READ_ALL_EVALUATIONS

    def _get_write_permission(self, resource_type: str) -> Permission:
        """Get appropriate write permission for resource type"""
        if resource_type == "evaluation":
            return Permission.WRITE_MANAGER_EVALUATION
        elif resource_type == "peer_feedback":
            return Permission.WRITE_PEER_FEEDBACK
        elif resource_type == "self_evaluation":
            return Permission.WRITE_SELF_EVAL
        else:
            return Permission.MANAGE_CYCLES
