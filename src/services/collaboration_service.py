#!/usr/bin/env python3
"""
团队协作服务
多角色权限、数据分享、操作日志、评论批注
"""

import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import Dict, List, Optional, Set

logger = logging.getLogger(__name__)


class Permission(Enum):
    READ = auto()
    WRITE = auto()
    DELETE = auto()
    MANAGE_USERS = auto()
    EXPORT = auto()


@dataclass
class Role:
    name: str
    permissions: Set[Permission] = field(default_factory=set)

    def has_permission(self, perm: Permission) -> bool:
        return perm in self.permissions


class RoleManager:
    def __init__(self):
        self._roles: Dict[str, Role] = {}
        self._register_defaults()

    def _register_defaults(self):
        self.register(
            Role(
                name="admin",
                permissions={
                    Permission.READ,
                    Permission.WRITE,
                    Permission.DELETE,
                    Permission.MANAGE_USERS,
                    Permission.EXPORT,
                },
            )
        )
        self.register(
            Role(
                name="analyst",
                permissions={Permission.READ, Permission.WRITE, Permission.EXPORT},
            )
        )
        self.register(
            Role(
                name="viewer",
                permissions={Permission.READ},
            )
        )

    def register(self, role: Role):
        self._roles[role.name] = role

    def get_role(self, name: str) -> Role:
        if name not in self._roles:
            raise KeyError(f"角色不存在: {name}")
        return self._roles[name]

    def list_roles(self) -> List[str]:
        return list(self._roles.keys())


@dataclass
class ShareRecord:
    share_id: str
    resource_type: str
    resource_id: str
    owner_id: str
    share_to: List[str]
    permission: str
    created_at: datetime = field(default_factory=datetime.now)
    active: bool = True


class ShareService:
    def __init__(self):
        self._shares: Dict[str, ShareRecord] = {}

    def create_share(
        self,
        resource_type: str,
        resource_id: str,
        owner_id: str,
        share_to: List[str],
        permission: str = "read",
    ) -> ShareRecord:
        record = ShareRecord(
            share_id=str(uuid.uuid4()),
            resource_type=resource_type,
            resource_id=resource_id,
            owner_id=owner_id,
            share_to=list(share_to),
            permission=permission,
        )
        self._shares[record.share_id] = record
        return record

    def get_shares_for_user(self, user_id: str) -> List[ShareRecord]:
        return [r for r in self._shares.values() if r.active and user_id in r.share_to]

    def revoke_share(self, share_id: str):
        if share_id in self._shares:
            self._shares[share_id].active = False

    def check_access(self, user_id: str, resource_type: str, resource_id: str) -> bool:
        return any(
            r.active
            and user_id in r.share_to
            and r.resource_type == resource_type
            and r.resource_id == resource_id
            for r in self._shares.values()
        )


@dataclass
class OperationLog:
    log_id: str
    user_id: str
    action: str
    resource_type: str
    resource_id: str
    detail: Dict = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)


class OperationLogger:
    def __init__(self):
        self._logs: List[OperationLog] = []

    def log(
        self,
        user_id: str,
        action: str,
        resource_type: str,
        resource_id: str,
        detail: Dict = None,
    ) -> OperationLog:
        entry = OperationLog(
            log_id=str(uuid.uuid4()),
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            detail=detail or {},
        )
        self._logs.append(entry)
        return entry

    def get_logs(
        self, user_id: str = None, resource_id: str = None
    ) -> List[OperationLog]:
        result = self._logs
        if user_id:
            result = [log_entry for log_entry in result if log_entry.user_id == user_id]
        if resource_id:
            result = [log_entry for log_entry in result if log_entry.resource_id == resource_id]
        return result

    def clear(self):
        self._logs.clear()


@dataclass
class Annotation:
    annotation_id: str
    resource_type: str
    resource_id: str
    user_id: str
    content: str
    position: Dict
    parent_id: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)


class AnnotationService:
    def __init__(self):
        self._annotations: Dict[str, Annotation] = {}

    def add(
        self,
        resource_type: str,
        resource_id: str,
        user_id: str,
        content: str,
        position: Dict,
    ) -> Annotation:
        ann = Annotation(
            annotation_id=str(uuid.uuid4()),
            resource_type=resource_type,
            resource_id=resource_id,
            user_id=user_id,
            content=content,
            position=position,
        )
        self._annotations[ann.annotation_id] = ann
        return ann

    def reply(self, parent_id: str, user_id: str, content: str) -> Annotation:
        parent = self._annotations.get(parent_id)
        if parent is None:
            raise KeyError(f"批注不存在: {parent_id}")
        ann = Annotation(
            annotation_id=str(uuid.uuid4()),
            resource_type=parent.resource_type,
            resource_id=parent.resource_id,
            user_id=user_id,
            content=content,
            position=parent.position,
            parent_id=parent_id,
        )
        self._annotations[ann.annotation_id] = ann
        return ann

    def get_by_resource(self, resource_type: str, resource_id: str) -> List[Annotation]:
        return [
            a
            for a in self._annotations.values()
            if a.resource_type == resource_type and a.resource_id == resource_id
        ]

    def delete(self, annotation_id: str):
        self._annotations.pop(annotation_id, None)
