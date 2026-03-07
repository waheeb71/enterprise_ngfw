#!/usr/bin/env python3
"""
Enterprise NGFW - Database Layer

SQLAlchemy models for persistent storage:
- User: user accounts with hashed passwords
- Rule: firewall rules
- Event: security events log
- AuditLog: admin action audit trail

Supports SQLite (dev) and PostgreSQL (production).
"""

import logging
from datetime import datetime
from typing import Optional, AsyncGenerator

from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime, Text, JSON,
    create_engine, event
)
from sqlalchemy.orm import (
    DeclarativeBase, sessionmaker, Session
)

logger = logging.getLogger(__name__)


# ==================== Base ====================

class Base(DeclarativeBase):
    """SQLAlchemy declarative base"""
    pass


# ==================== Models ====================

class User(Base):
    """User account"""
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(64), unique=True, nullable=False, index=True)
    password_hash = Column(String(256), nullable=False)
    role = Column(String(32), nullable=False, default='viewer')
    email = Column(String(128), nullable=True)
    display_name = Column(String(128), nullable=True)
    is_active = Column(Boolean, default=True)
    is_ldap = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)

    def __repr__(self):
        return f"<User {self.username} ({self.role})>"


class Rule(Base):
    """Firewall rule"""
    __tablename__ = 'rules'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(128), nullable=True)
    src_ip = Column(String(64), nullable=True)
    dst_ip = Column(String(64), nullable=True)
    src_port = Column(Integer, nullable=True)
    dst_port = Column(Integer, nullable=True)
    protocol = Column(String(10), nullable=True)
    action = Column(String(20), nullable=False, default='BLOCK')
    priority = Column(Integer, default=50)
    enabled = Column(Boolean, default=True)
    description = Column(Text, nullable=True)
    created_by = Column(String(64), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'src_ip': self.src_ip,
            'dst_ip': self.dst_ip,
            'src_port': self.src_port,
            'dst_port': self.dst_port,
            'protocol': self.protocol,
            'action': self.action,
            'priority': self.priority,
            'enabled': self.enabled,
            'description': self.description,
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self):
        return f"<Rule #{self.id} {self.action} {self.src_ip}→{self.dst_port}>"


class SecurityEvent(Base):
    """Security event log"""
    __tablename__ = 'security_events'

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    event_type = Column(String(32), nullable=False, index=True)
    severity = Column(String(16), nullable=False, default='info')
    source_ip = Column(String(64), nullable=True, index=True)
    destination_ip = Column(String(64), nullable=True)
    source_port = Column(Integer, nullable=True)
    destination_port = Column(Integer, nullable=True)
    protocol = Column(String(10), nullable=True)
    action = Column(String(20), nullable=True)
    description = Column(Text, nullable=True)
    anomaly_score = Column(Float, nullable=True)
    event_metadata = Column(JSON, nullable=True)

    def to_dict(self):
        return {
            'id': self.id,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'event_type': self.event_type,
            'severity': self.severity,
            'source_ip': self.source_ip,
            'destination_ip': self.destination_ip,
            'action': self.action,
            'description': self.description,
            'anomaly_score': self.anomaly_score,
        }


class AuditLog(Base):
    """Admin action audit trail"""
    __tablename__ = 'audit_log'

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    username = Column(String(64), nullable=False, index=True)
    action = Column(String(64), nullable=False)
    resource = Column(String(128), nullable=True)
    details = Column(JSON, nullable=True)
    ip_address = Column(String(64), nullable=True)


# ==================== Database Manager ====================

class DatabaseManager:
    """
    Database connection and session management

    Usage:
        db = DatabaseManager('sqlite:///ngfw.db')
        db.initialize()

        with db.session() as session:
            user = session.query(User).filter_by(username='admin').first()
    """

    def __init__(self, database_url: str = 'sqlite:///ngfw.db'):
        self.database_url = database_url
        self.engine = None
        self._session_factory = None
        logger.info(f"DatabaseManager initialized: {database_url.split('://')[0]}")

    def initialize(self):
        """Create engine, tables, and session factory"""
        self.engine = create_engine(
            self.database_url,
            echo=False,
            pool_pre_ping=True
        )

        # Create all tables
        Base.metadata.create_all(self.engine)

        self._session_factory = sessionmaker(bind=self.engine)
        logger.info("Database tables created")

    def session(self) -> Session:
        """Get a database session"""
        if not self._session_factory:
            self.initialize()
        return self._session_factory()

    def add_default_users(self, admin_hash: str, operator_hash: str):
        """Add default users if they don't exist"""
        with self.session() as session:
            if not session.query(User).filter_by(username='admin').first():
                session.add(User(
                    username='admin',
                    password_hash=admin_hash,
                    role='admin',
                    display_name='Administrator'
                ))
            if not session.query(User).filter_by(username='operator').first():
                session.add(User(
                    username='operator',
                    password_hash=operator_hash,
                    role='operator',
                    display_name='Operator'
                ))
            session.commit()
        logger.info("Default users ensured")

    def close(self):
        """Close database connection"""
        if self.engine:
            self.engine.dispose()
            logger.info("Database connection closed")
